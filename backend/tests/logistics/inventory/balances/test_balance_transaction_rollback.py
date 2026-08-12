"""
test_balance_transaction_rollback.py — Rollback DB real (Fase 045)

CRITERIO DE EVIDENCIA:
- Engine PostgreSQL real
- Session real con BEGIN / INSERT / COMMIT
- Segunda transacción: INSERT balance + INSERT delta → forzar error → ROLLBACK
- Nueva sesión: verificar que balance original persiste
- Verificar que delta fallido NO fue persistido
- Verificar que cursor NO avanzó
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryBalanceProjectionCursorModel,
    InventoryPositionBalanceModel,
)

pytestmark = pytest.mark.postgres


@pytest.mark.postgres
def test_transactional_rollback_db_real(pg_engine):
    """
    ROLLBACK DB REAL.

    Flujo:
    1. Insertar balance inicial = 100 en DB — COMMIT (persistido).
    2. Insertar cursor inicial con last_applied_sequence=1000 — COMMIT.
    3. Abrir nueva transacción:
       a. Actualizar balance quantity → 70 (-30).
       b. Insertar InventoryBalanceDeltaModel con sequence=1001.
       c. Simular error productivo (no actualizar cursor — error forzado).
       d. ROLLBACK explícito.
    4. Abrir nueva sesión:
       a. Verificar balance = 100 (no 70).
       b. Verificar COUNT(delta para pos_id) = 0 (no persistido).
       c. Verificar cursor last_applied_sequence = 1000 (no avanzó).
    """
    org_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    user_id = uuid4()
    partition_key = f"org:{org_id}:wh:default"

    # Paso 1: Persistir balance inicial
    with Session(pg_engine) as session_setup:
        balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=uuid4(),
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("100.000000000000000000"),
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=partition_key,
            last_applied_ledger_sequence=1000,
        )
        session_setup.add(balance)

        # Cursor inicial
        cursor = InventoryBalanceProjectionCursorModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=partition_key,
            last_applied_sequence=1000,
            status="CURRENT",
        )
        session_setup.add(cursor)
        session_setup.commit()

    # Paso 2: Transacción que falla a mitad
    with Session(pg_engine) as session_fail:
        try:
            # Leer balance con lock
            from sqlalchemy import select
            stmt = (
                select(InventoryPositionBalanceModel)
                .where(InventoryPositionBalanceModel.inventory_position_id == pos_id)
                .with_for_update()
            )
            balance_row = session_fail.execute(stmt).scalar_one()

            # Actualizar balance
            balance_row.quantity = Decimal("70.000000000000000000")

            # Insertar delta
            mov_id = uuid4()
            line_id = uuid4()
            delta = InventoryBalanceDeltaModel(
                id=uuid4(),
                organization_id=org_id,
                ledger_partition_key=partition_key,
                ledger_sequence=1001,
                movement_id=mov_id,
                movement_line_id=line_id,
                position_id=pos_id,
                product_id=prod_id,
                base_unit_id=unit_id,
                delta_type="DECREASE",
                delta_quantity=Decimal("30.000000000000000000"),
                movement_hash="dd" * 32,  # 64 chars
                materialization_key=f"mat_delta:{mov_id}:{line_id}:{pos_id}:DECREASE",
                applied_status="APPLIED",
            )
            session_fail.add(delta)

            # Simular error productivo — forzar excepción antes de actualizar cursor
            raise RuntimeError(
                "SIMULATED_PRODUCTION_ERROR: Cursor update failed due to hash mismatch. "
                "Rolling back entire transaction."
            )

        except RuntimeError:
            # ROLLBACK explícito
            session_fail.rollback()

    # Paso 3: Verificar estado DB desde nueva sesión
    with Session(pg_engine) as session_verify:
        # Balance debe ser 100 (no 70)
        balance_after = session_verify.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()

        assert balance_after.quantity == Decimal("100.000000000000000000"), (
            f"ROLLBACK FAIL: Se esperaba balance=100 después del rollback, "
            f"pero DB tiene balance={balance_after.quantity}. "
            f"El ROLLBACK no fue efectivo."
        )

        # Delta NO debe existir en DB
        delta_count = session_verify.query(
            func.count(InventoryBalanceDeltaModel.id)
        ).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).scalar()

        assert delta_count == 0, (
            f"ROLLBACK FAIL: Se esperaba COUNT(delta)=0 después del rollback, "
            f"pero DB tiene COUNT={delta_count}. "
            f"El delta fue persistido a pesar del ROLLBACK."
        )

        # Cursor NO debe haber avanzado
        cursor_after = session_verify.query(InventoryBalanceProjectionCursorModel).filter(
            InventoryBalanceProjectionCursorModel.organization_id == org_id,
            InventoryBalanceProjectionCursorModel.ledger_partition_key == partition_key,
        ).one()

        assert cursor_after.last_applied_sequence == 1000, (
            f"ROLLBACK FAIL: El cursor avanzó a {cursor_after.last_applied_sequence} "
            f"a pesar del ROLLBACK. Se esperaba last_applied_sequence=1000."
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).delete()
        cleanup.query(InventoryBalanceProjectionCursorModel).filter(
            InventoryBalanceProjectionCursorModel.organization_id == org_id
        ).delete()
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.commit()
