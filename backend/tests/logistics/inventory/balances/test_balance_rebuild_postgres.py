"""
test_balance_rebuild_postgres.py — Rebuild real desde DB (Fase 045)

CRITERIO DE EVIDENCIA:
- Persistir InventoryPositionBalanceModel real en PostgreSQL
- Persistir InventoryBalanceDeltaModel reales (+100, -30, +20)
- Corromper la proyección (UPDATE quantity = 0 directamente en DB)
- Releer deltas reales desde DB
- Ejecutar RebuildService.replay_movements_and_calculate con datos reales de DB
- Verificar que el saldo recalculado = 90
- Verificar que la proyección corrompida puede ser restaurada
- REBUILD_SWAP_NOT_IMPLEMENTED: documentado (no existe atomic swap en capa actual)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.domain.services.rebuild_service import RebuildService
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryPositionBalanceModel,
)

pytestmark = pytest.mark.postgres


@pytest.mark.postgres
def test_rebuild_reads_deltas_from_real_db_and_restores_balance(pg_engine):
    """
    REBUILD REAL desde PostgreSQL.

    Flujo:
    1. Insertar InventoryPositionBalanceModel con quantity=0 en DB.
    2. Insertar 3 InventoryBalanceDeltaModel: +100, -30, +20.
    3. COMMIT — datos persisten en DB.
    4. Releer deltas desde DB (SELECT real).
    5. Ejecutar RebuildService.replay_movements_and_calculate con datos reales.
    6. Verificar que el saldo calculado = 90.
    7. Aplicar corrección (UPDATE) al balance proyectado.
    8. Verificar persistencia de la corrección desde nueva sesión.
    """
    org_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    partition_key = f"org:{org_id}:wh:default"

    # Paso 1: Insertar balance inicial
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

        # Insertar 3 deltas reales: +100, -30, +20
        deltas_data = [
            ("INCREASE", Decimal("100.000000000000000000"), 1001),
            ("DECREASE", Decimal("30.000000000000000000"), 1002),
            ("INCREASE", Decimal("20.000000000000000000"), 1003),
        ]

        for direction, qty, seq in deltas_data:
            mov_id = uuid4()
            line_id = uuid4()
            key = f"mat_delta:{mov_id}:{line_id}:{pos_id}:{direction}"
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
                movement_hash="aabbccdd11223344" * 4,  # 64 chars
                materialization_key=key,
                applied_status="APPLIED",
            )
            session_setup.add(delta)

        session_setup.commit()

    # Paso 2: Simular proyección corrompida (quantity = 999)
    with Session(pg_engine) as session_corrupt:
        session_corrupt.execute(
            text(
                "UPDATE inventory_position_balances SET quantity = :qty "
                "WHERE inventory_position_id = :pos_id"
            ),
            {"qty": Decimal("999.000000000000000000"), "pos_id": str(pos_id)},
        )
        session_corrupt.commit()

    # Verificar que la corrupción fue aplicada
    with Session(pg_engine) as session_check:
        row_corrupted = session_check.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()
        assert row_corrupted.quantity == Decimal("999.000000000000000000"), (
            "La proyección no fue corrompida correctamente para la prueba"
        )

    # Paso 3: Releer deltas REALES desde DB (esto es la parte crítica)
    with Session(pg_engine) as session_rebuild:
        delta_rows = session_rebuild.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).order_by(InventoryBalanceDeltaModel.ledger_sequence).all()

        # Convertir a formato que entiende RebuildService
        movement_lines = [
            {
                "position_id": str(row.position_id),
                "quantity": str(row.delta_quantity),
                "direction": row.delta_type,
            }
            for row in delta_rows
        ]

    # Paso 4: Ejecutar RebuildService con datos reales leídos de DB
    service = RebuildService()
    recalculated = service.replay_movements_and_calculate(movement_lines)

    expected_qty = Decimal("90.000000000000000000")
    pos_key = str(pos_id)
    assert pos_key in recalculated, (
        f"REBUILD FAIL: La posición {pos_key} no aparece en el resultado del rebuild"
    )
    assert recalculated[pos_key] == expected_qty, (
        f"REBUILD FAIL: Saldo esperado=90, obtenido={recalculated[pos_key]}. "
        f"Deltas leídos de DB: {[(ml['direction'], ml['quantity']) for ml in movement_lines]}"
    )

    # Paso 5: Aplicar la corrección a la DB (simular swap)
    with Session(pg_engine) as session_apply:
        session_apply.execute(
            text(
                "UPDATE inventory_position_balances SET quantity = :qty "
                "WHERE inventory_position_id = :pos_id"
            ),
            {"qty": expected_qty, "pos_id": str(pos_id)},
        )
        session_apply.commit()

    # Paso 6: Verificar persistencia desde nueva sesión
    with Session(pg_engine) as session_final:
        row_final = session_final.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()
        assert row_final.quantity == expected_qty, (
            f"REBUILD PERSISTENCE FAIL: Saldo en DB después de restore = {row_final.quantity}, "
            f"esperado = {expected_qty}"
        )

    # REBUILD_SWAP_NOT_IMPLEMENTED:
    # El BalanceProjectionService / RebuildService actual no implementa
    # el "atomic swap" (crear proyección temporal + swap atómico en una transacción).
    # El rebuild actual lee deltas de DB y recalcula con el servicio domain,
    # luego el test aplica el resultado directamente. Clasificación: REBUILD_SWAP_NOT_IMPLEMENTED.

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).delete()
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.commit()
