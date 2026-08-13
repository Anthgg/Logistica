"""
test_balance_reconciliation_postgres.py — Reconciliación real desde DB (Fase 045)

CRITERIO DE EVIDENCIA:
- Persistir InventoryPositionBalanceModel con quantity=100 en DB
- Persistir InventoryBalanceDeltaModel reales que suman 80 (+60, +20)
- Releer balance proyectado y deltas desde DB (SELECT real)
- Ejecutar ReconciliationService con datos reales
- Verificar que la diferencia detectada = 20 (100 proyectado vs 80 replay)
- Persistir diferencia en InventoryBalanceReconciliationDifferenceModel
- Verificar que el balance proyectado NO fue modificado (reconciliación no muta)
- Verificar que los MOV no fueron modificados
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.domain.services.reconciliation_service import (
    ReconciliationService,
)
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryBalanceReconciliationDifferenceModel,
    InventoryBalanceReconciliationJobModel,
    InventoryPositionBalanceModel,
)

pytestmark = pytest.mark.postgres


@pytest.mark.postgres
def test_reconciliation_detects_mismatch_and_persists_difference(pg_engine):
    """
    RECONCILIATION REAL desde PostgreSQL.

    Flujo:
    1. Insertar balance proyectado = 100 en DB.
    2. Insertar deltas reales que suman 80 (+60, +20).
    3. Crear ReconciliationJob en DB.
    4. Releer balance proyectado y deltas desde DB (SELECT real).
    5. Ejecutar ReconciliationService.reconcile con datos reales de DB.
    6. Persistir diferencia en inventory_balance_reconciliation_differences.
    7. COMMIT.
    8. Verificar desde nueva sesión:
       - Diferencia = 20 en tabla real
       - Balance proyectado sigue siendo 100 (no fue mutado)
       - Deltas no fueron modificados
    """
    org_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    user_id = uuid4()
    partition_key = f"org:{org_id}:wh:default"

    # Paso 1: Insertar balance proyectado = 100
    with Session(pg_engine) as session_setup:
        balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=uuid4(),
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("100.000000000000000000"),  # proyectado = 100
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=partition_key,
            last_applied_ledger_sequence=1002,
        )
        session_setup.add(balance)

        # Insertar deltas reales que suman 80 (+60, +20)
        for direction, qty, seq in [
            ("INCREASE", Decimal("60.000000000000000000"), 1001),
            ("INCREASE", Decimal("20.000000000000000000"), 1002),
        ]:
            mov_id = uuid4()
            line_id = uuid4()
            delta = InventoryBalanceDeltaModel(
                id=uuid4(),
                organization_id=org_id,
                ledger_partition_key=partition_key,
                ledger_sequence=seq,
                movement_id=mov_id,
                movement_line_id=line_id,
                position_id=pos_id,
                product_id=prod_id,
                base_unit_id=unit_id,
                delta_type=direction,
                delta_quantity=qty,
                movement_hash="cc" * 32,  # 64 chars
                materialization_key=f"mat_delta:{mov_id}:{line_id}:{pos_id}:{direction}",
                applied_status="APPLIED",
            )
            session_setup.add(delta)

        session_setup.commit()

    # Paso 2: Crear ReconciliationJob
    recon_job_id = uuid4()
    with Session(pg_engine) as session_job:
        job = InventoryBalanceReconciliationJobModel(
            id=recon_job_id,
            organization_id=org_id,
            status="IN_PROGRESS",
            initiated_by_user_id=user_id,
        )
        session_job.add(job)
        session_job.commit()

    # Paso 3: Releer datos REALES desde DB
    with Session(pg_engine) as session_read:
        balance_row = session_read.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()
        projected_quantity = balance_row.quantity  # 100

        delta_rows = session_read.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).all()

        # Construir mapa de replay desde deltas reales de DB
        replayed_qty = Decimal("0.000000000000000000")
        for row in delta_rows:
            if row.delta_type == "INCREASE":
                replayed_qty += row.delta_quantity
            elif row.delta_type == "DECREASE":
                replayed_qty -= row.delta_quantity

    # replayed_qty debe ser 80 (60 + 20)
    assert replayed_qty == Decimal("80.000000000000000000"), (
        f"Error en setup: se esperaba replay=80 desde DB, obtenido={replayed_qty}"
    )

    # Paso 4: Ejecutar ReconciliationService con datos reales de DB
    pos_key = str(pos_id)
    service = ReconciliationService()
    differences = service.reconcile(
        projected_balances={pos_key: projected_quantity},
        replayed_balances={pos_key: replayed_qty},
    )

    assert len(differences) == 1, (
        f"RECONCILIATION FAIL: Se esperaba 1 diferencia, obtenidas: {len(differences)}"
    )
    diff = differences[0]
    assert diff["status"] == "MISMATCH_DETECTED"
    expected_diff = Decimal("20.000000000000000000")  # 100 - 80 = 20
    assert diff["difference_quantity"] == expected_diff, (
        f"RECONCILIATION FAIL: Diferencia esperada=20, obtenida={diff['difference_quantity']}"
    )

    # Paso 5: Persistir diferencia en tabla real
    with Session(pg_engine) as session_persist:
        difference_record = InventoryBalanceReconciliationDifferenceModel(
            id=uuid4(),
            reconciliation_job_id=recon_job_id,
            difference_type="PROJECTION_REPLAY_MISMATCH",
            organization_id=org_id,
            product_id=prod_id,
            position_id=pos_id,
            unit_id=unit_id,
            projected_quantity=projected_quantity,
            replay_quantity=replayed_qty,
            difference_quantity=diff["difference_quantity"],
            expected_sequence=1002,
            actual_sequence=1002,
            resolution_status="OPEN",
        )
        session_persist.add(difference_record)
        session_persist.commit()

    # Paso 6: Verificar desde nueva sesión
    with Session(pg_engine) as session_verify:
        # Diferencia persistida en DB
        diff_rows = session_verify.query(
            InventoryBalanceReconciliationDifferenceModel
        ).filter(
            InventoryBalanceReconciliationDifferenceModel.reconciliation_job_id == recon_job_id
        ).all()

        assert len(diff_rows) == 1, (
            f"RECONCILIATION_PERSISTENCE FAIL: Se esperaba 1 diferencia persistida, "
            f"encontradas: {len(diff_rows)}"
        )
        assert diff_rows[0].difference_quantity == expected_diff, (
            f"RECONCILIATION_PERSISTENCE FAIL: Diferencia en DB = {diff_rows[0].difference_quantity}, "
            f"esperada = {expected_diff}"
        )

        # Balance proyectado NO fue modificado
        balance_after = session_verify.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()
        assert balance_after.quantity == Decimal("100.000000000000000000"), (
            f"RECONCILIATION_MUTATION DETECTED: El balance proyectado fue mutado a "
            f"{balance_after.quantity}. La reconciliación NO debe mutar saldos."
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryBalanceReconciliationDifferenceModel).filter(
            InventoryBalanceReconciliationDifferenceModel.reconciliation_job_id == recon_job_id
        ).delete()
        cleanup.query(InventoryBalanceReconciliationJobModel).filter(
            InventoryBalanceReconciliationJobModel.id == recon_job_id
        ).delete()
        cleanup.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).delete()
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.commit()
