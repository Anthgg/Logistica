"""
test_balance_sequence_gap_postgres.py — Sequence gap real con cursor DB (Fase 045)

CRITERIO DE EVIDENCIA:
- Persistir InventoryBalanceProjectionCursorModel real en DB
- Persistir InventoryBalanceDeltaModel con secuencias 1001, 1002, 1004 (gap)
- Simular consumer que detiene el cursor al detectar el gap
- Verificar cursor detenido en 1002 en DB real
- Insertar secuencia faltante 1003
- Simular consumer nuevamente
- Verificar cursor avanzó a 1004 en DB real
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryBalanceProjectionCursorModel,
    InventoryPositionBalanceModel,
)

pytestmark = pytest.mark.postgres


def _consume_deltas_ordered(session: Session, org_id, partition_key: str, pos_id) -> None:
    """
    Consumer que lee deltas ordenados por sequence y aplica hasta detectar un gap.
    Actualiza el cursor en DB.
    """
    cursor = session.query(InventoryBalanceProjectionCursorModel).filter(
        InventoryBalanceProjectionCursorModel.organization_id == org_id,
        InventoryBalanceProjectionCursorModel.ledger_partition_key == partition_key,
    ).with_for_update().one()

    last_seq = cursor.last_applied_sequence

    # Leer deltas pendientes desde DB
    pending_deltas = session.query(InventoryBalanceDeltaModel).filter(
        InventoryBalanceDeltaModel.position_id == pos_id,
        InventoryBalanceDeltaModel.ledger_sequence > last_seq,
        InventoryBalanceDeltaModel.applied_status == "PENDING",
    ).order_by(InventoryBalanceDeltaModel.ledger_sequence).all()

    balance_row = session.query(InventoryPositionBalanceModel).filter(
        InventoryPositionBalanceModel.inventory_position_id == pos_id
    ).with_for_update().one()

    for delta in pending_deltas:
        if delta.ledger_sequence != last_seq + 1:
            # GAP DETECTED — detener consumer, marcar cursor
            cursor.last_applied_sequence = last_seq
            cursor.status = "GAP_DETECTED"
            session.commit()
            return

        # Aplicar delta
        if delta.delta_type == "INCREASE":
            balance_row.quantity += delta.delta_quantity
        else:
            balance_row.quantity -= delta.delta_quantity

        delta.applied_status = "APPLIED"
        last_seq = delta.ledger_sequence

    cursor.last_applied_sequence = last_seq
    cursor.status = "CURRENT"
    session.commit()


@pytest.mark.postgres
def test_sequence_gap_halts_cursor_in_db(pg_engine):
    """
    SEQUENCE GAP REAL en PostgreSQL.

    Flujo:
    1. Cursor en DB con last_applied_sequence=1000.
    2. Insertar deltas con secuencias 1001, 1002, 1004 (gap — falta 1003).
    3. Ejecutar consumer real.
    4. Verificar que el cursor se detuvo en 1002 (GAP_DETECTED).
    5. Insertar delta faltante 1003.
    6. Ejecutar consumer nuevamente.
    7. Verificar cursor en 1004 (CURRENT).
    """
    org_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    partition_key = f"org:{org_id}:wh:default"

    # Paso 1: Setup — balance + cursor iniciales
    with Session(pg_engine) as session_setup:
        balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=uuid4(),
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("0.000000000000000000"),
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=partition_key,
            last_applied_ledger_sequence=1000,
        )
        session_setup.add(balance)

        cursor = InventoryBalanceProjectionCursorModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=partition_key,
            last_applied_sequence=1000,
            status="CURRENT",
        )
        session_setup.add(cursor)

        # Insertar deltas: 1001, 1002, 1004 (falta 1003)
        for seq in [1001, 1002, 1004]:
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
                delta_type="INCREASE",
                delta_quantity=Decimal("10.000000000000000000"),
                movement_hash="ee" * 32,  # 64 chars
                materialization_key=f"mat_delta:{mov_id}:{line_id}:{pos_id}:INCREASE:seq{seq}",
                applied_status="PENDING",
            )
            session_setup.add(delta)

        session_setup.commit()

    # Paso 2: Ejecutar consumer — debe detenerse en gap
    with Session(pg_engine) as session_consumer:
        _consume_deltas_ordered(session_consumer, org_id, partition_key, pos_id)

    # Paso 3: Verificar cursor detenido en 1002
    with Session(pg_engine) as session_verify1:
        cursor_row = session_verify1.query(InventoryBalanceProjectionCursorModel).filter(
            InventoryBalanceProjectionCursorModel.organization_id == org_id,
            InventoryBalanceProjectionCursorModel.ledger_partition_key == partition_key,
        ).one()

        assert cursor_row.last_applied_sequence == 1002, (
            f"GAP_DETECTION FAIL: El cursor debería estar en 1002 (antes del gap), "
            f"pero está en {cursor_row.last_applied_sequence}"
        )
        assert cursor_row.status == "GAP_DETECTED", (
            f"GAP_DETECTION FAIL: El cursor debería tener status=GAP_DETECTED, "
            f"pero tiene status={cursor_row.status}"
        )

        # Secuencia 1004 aún PENDING en DB
        delta_1004 = session_verify1.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id,
            InventoryBalanceDeltaModel.ledger_sequence == 1004,
        ).one()
        assert delta_1004.applied_status == "PENDING", (
            f"GAP FAIL: El delta 1004 no debería estar aplicado antes de resolver el gap. "
            f"Estado actual: {delta_1004.applied_status}"
        )

    # Paso 4: Insertar delta faltante 1003 (recuperación de gap)
    with Session(pg_engine) as session_fill_gap:
        mov_id_1003 = uuid4()
        line_id_1003 = uuid4()
        delta_1003 = InventoryBalanceDeltaModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=partition_key,
            ledger_sequence=1003,
            movement_id=mov_id_1003,
            movement_line_id=line_id_1003,
            position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            delta_type="INCREASE",
            delta_quantity=Decimal("10.000000000000000000"),
            movement_hash="ff" * 32,
            materialization_key=f"mat_delta:{mov_id_1003}:{line_id_1003}:{pos_id}:INCREASE:seq1003",
            applied_status="PENDING",
        )
        session_fill_gap.add(delta_1003)
        session_fill_gap.commit()

    # Paso 5: Ejecutar consumer nuevamente
    with Session(pg_engine) as session_consumer2:
        _consume_deltas_ordered(session_consumer2, org_id, partition_key, pos_id)

    # Paso 6: Verificar cursor avanzó a 1004
    with Session(pg_engine) as session_verify2:
        cursor_final = session_verify2.query(InventoryBalanceProjectionCursorModel).filter(
            InventoryBalanceProjectionCursorModel.organization_id == org_id,
            InventoryBalanceProjectionCursorModel.ledger_partition_key == partition_key,
        ).one()

        assert cursor_final.last_applied_sequence == 1004, (
            f"GAP_RECOVERY FAIL: El cursor debería estar en 1004 después de resolver el gap, "
            f"pero está en {cursor_final.last_applied_sequence}"
        )
        assert cursor_final.status == "CURRENT", (
            f"GAP_RECOVERY FAIL: El cursor debería tener status=CURRENT, "
            f"pero tiene status={cursor_final.status}"
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
