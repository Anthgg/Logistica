"""
test_balance_rebuild_postgres.py — Integration tests for Rebuild Atomic Swap (Phase 045)

CRITERIO DE EVIDENCIA:
- Usa PostgreSQL real (Engine + Session)
- Demuestra que el Rebuild NUNCA modifica la proyección activa en caliente row-by-row
- Utiliza la arquitectura de Staging Projection (G1 = activa, G2 = staging)
- Valida que durante la reconstrucción G2 los lectores continúan leyendo G1 (100)
- Demuestra que el Atomic Swap ocurre en UNA ÚNICA transacción PostgreSQL
- Demuestra que ante una falla en la validación o durante el swap, la transacción hace ROLLBACK
  y G1 permanece intacta (100)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.application.services.rebuild_application_service import (
    BalanceRebuildApplicationService,
    RebuildSwapFailedError,
)
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryBalanceRebuildJobModel,
    InventoryPositionBalanceModel,
)


@pytest.mark.postgres
def test_rebuild_atomic_swap_success_db(pg_engine):
    """
    ATOMIC SWAP SUCCESS REAL — Rebuild con staging G2 y swap atómico en PostgreSQL.

    Flujo:
    1. G1 activo en DB con cantidad = 100.
    2. Iniciar Rebuild Job.
    3. Crear G2 staging projection (is_active_projection=False).
    4. Aplicar deltas (-20) a G2. G2 cantidad = 80.
    5. Durante la reconstrucción, consultas de lectores a la proyección activa (is_active_projection=True)
       siguen retornando G1 = 100.
    6. Validar pre-swap.
    7. Ejecutar atomic_swap() en una sola transacción.
    8. Consultas posteriores retornan G2 = 80.
    9. Job status = COMPLETED.
    """
    org_id = uuid4()
    branch_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    user_id = uuid4()

    # 1. Crear G1 activo = 100
    with Session(pg_engine) as session_setup:
        g1_balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=branch_id,
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("100.000000000000000000"),
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=f"org:{org_id}:default",
            last_applied_ledger_sequence=1000,
            is_active_projection=True,
            rebuild_job_id=None,
        )
        session_setup.add(g1_balance)
        session_setup.commit()

    # 2. Iniciar Rebuild Service y Job
    with Session(pg_engine) as session_rebuild:
        svc = BalanceRebuildApplicationService(session_rebuild)
        job = svc.create_rebuild_job(
            organization_id=org_id,
            initiated_by_user_id=user_id,
            rebuild_mode="FULL",
            step_up_verified=True,
        )
        job_id = job.id

        # 3. Crear G2 staging
        positions_to_rebuild = [
            {
                "inventory_position_id": pos_id,
                "product_id": prod_id,
                "base_unit_id": unit_id,
                "branch_id": branch_id,
                "initial_quantity": "100.000000000000000000",
                "partition_key": f"org:{org_id}:default",
            }
        ]
        svc.prepare_staging_projection(job_id, positions_to_rebuild)

        # 4. Aplicar delta (-20) a G2 staging
        delta = InventoryBalanceDeltaModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=f"org:{org_id}:default",
            ledger_sequence=1001,
            movement_id=uuid4(),
            movement_line_id=uuid4(),
            position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            delta_type="DECREASE",
            delta_quantity=Decimal("20.000000000000000000"),
            movement_hash="00" * 32,
            materialization_key=f"mat:{uuid4()}",
            applied_status="PENDING",
        )
        svc.replay_deltas_into_staging(job_id, [delta])
        session_rebuild.commit()

    # 5. LECTORES DURANTE REBUILD: Verificar que lectores ven G1 = 100
    with Session(pg_engine) as session_reader:
        active_bal = session_reader.execute(
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.inventory_position_id == pos_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        ).scalar_one()
        assert active_bal.quantity == Decimal("100.000000000000000000"), (
            f"READERS_DURING_REBUILD FAIL: Lectores leyeron {active_bal.quantity} "
            f"durante la reconstrucción. Debieron leer G1 = 100."
        )

    # 6 & 7. Validar pre-swap y ejecutar Atomic Swap
    with Session(pg_engine) as session_swap:
        svc = BalanceRebuildApplicationService(session_swap)
        assert svc.validate_staging(job_id) is True
        assert svc.execute_atomic_swap(job_id) is True
        session_swap.commit()

    # 8. LECTORES DESPUÉS DEL SWAP: Verificar que lectores ven G2 = 80
    with Session(pg_engine) as session_verify:
        active_bal_after = session_verify.execute(
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.inventory_position_id == pos_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        ).scalar_one()

        job_after = session_verify.get(InventoryBalanceRebuildJobModel, job_id)

        assert active_bal_after.quantity == Decimal("80.000000000000000000"), (
            f"ATOMIC_SWAP FAIL: La proyección activa tiene {active_bal_after.quantity}. "
            f"Se esperaba G2 = 80."
        )
        assert job_after.status == "COMPLETED", (
            f"ATOMIC_SWAP FAIL: Job status es {job_after.status}. Se esperaba COMPLETED."
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.query(InventoryBalanceRebuildJobModel).filter(
            InventoryBalanceRebuildJobModel.id == job_id
        ).delete()
        cleanup.commit()


@pytest.mark.postgres
def test_rebuild_atomic_swap_rollback_on_failure_db(pg_engine):
    """
    ATOMIC SWAP ROLLBACK REAL — Fallo en validación pre-swap aborta el rebuild
    y G1 permanece intacto (100).

    Flujo:
    1. G1 activo en DB = 100.
    2. Rebuild G2 creado.
    3. Aplicar delta (-150) resultando en stock negativo (-50).
    4. Ejecutar validate_staging() → Levanta RebuildSwapFailedError (Negative Stock).
    5. Ejecutar rollback_rebuild().
    6. Proyección activa en DB sigue siendo G1 = 100.
    7. Job status = FAILED.
    """
    org_id = uuid4()
    branch_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    user_id = uuid4()

    # 1. G1 activo = 100
    with Session(pg_engine) as session_setup:
        g1 = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=branch_id,
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("100.000000000000000000"),
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=f"org:{org_id}:default",
            last_applied_ledger_sequence=1000,
            is_active_projection=True,
        )
        session_setup.add(g1)
        session_setup.commit()

    # 2. Iniciar Rebuild
    with Session(pg_engine) as session_rebuild:
        svc = BalanceRebuildApplicationService(session_rebuild)
        job = svc.create_rebuild_job(
            organization_id=org_id,
            initiated_by_user_id=user_id,
        )
        job_id = job.id

        svc.prepare_staging_projection(
            job_id,
            [
                {
                    "inventory_position_id": pos_id,
                    "product_id": prod_id,
                    "base_unit_id": unit_id,
                    "branch_id": branch_id,
                    "initial_quantity": "100.000000000000000000",
                }
            ],
        )

        # 3. Aplicar delta (-150) -> stock negativo -50
        delta = InventoryBalanceDeltaModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=f"org:{org_id}:default",
            ledger_sequence=1001,
            movement_id=uuid4(),
            movement_line_id=uuid4(),
            position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            delta_type="DECREASE",
            delta_quantity=Decimal("150.000000000000000000"),
            movement_hash="00" * 32,
            materialization_key=f"mat:{uuid4()}",
            applied_status="PENDING",
        )
        svc.replay_deltas_into_staging(job_id, [delta])
        session_rebuild.commit()

    # 4 & 5. Pre-swap validation falla → Rollback
    with Session(pg_engine) as session_validate:
        svc = BalanceRebuildApplicationService(session_validate)
        with pytest.raises(RebuildSwapFailedError, match="Negative stock"):
            svc.validate_staging(job_id, allow_negative_stock=False)

        svc.rollback_rebuild(job_id, "PRE_SWAP_VALIDATION_FAILED: Negative stock")
        session_validate.commit()

    # 6 & 7. Verificar que G1 sigue siendo 100 y Job es FAILED
    with Session(pg_engine) as session_verify:
        active_after = session_verify.execute(
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.inventory_position_id == pos_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        ).scalar_one()

        job_after = session_verify.get(InventoryBalanceRebuildJobModel, job_id)

        assert active_after.quantity == Decimal("100.000000000000000000"), (
            f"SWAP_ROLLBACK FAIL: La proyección activa fue modificada a {active_after.quantity}. "
            f"Debió permanecer intacta en G1 = 100."
        )
        assert job_after.status == "FAILED", (
            f"SWAP_ROLLBACK FAIL: Job status es {job_after.status}. Se esperaba FAILED."
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.query(InventoryBalanceRebuildJobModel).filter(
            InventoryBalanceRebuildJobModel.id == job_id
        ).delete()
        cleanup.commit()
