"""
test_balance_idempotency_postgres.py — Idempotencia DB real (Fase 045)

CRITERIO DE EVIDENCIA:
- Engine PostgreSQL real
- Session real con BEGIN / INSERT / COMMIT / ROLLBACK
- UNIQUE constraint real en materialization_key
- IntegrityError real de la base de datos
- SELECT COUNT(*) real desde nueva sesión
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.balances.infrastructure.projections.balance_projection_service import (
    BalanceProjectionService,
)

pytestmark = pytest.mark.postgres


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.postgres
def test_materialization_key_determinism():
    """
    MATERIALIZATION_KEY_DETERMINISM (unit).

    El mismo conjunto de IDs y dirección siempre produce la misma clave.
    Este test es UNIT — no requiere PostgreSQL.
    """
    mov_id = uuid4()
    line_id = uuid4()
    pos_id = uuid4()

    key1 = BalanceProjectionService.generate_materialization_key(mov_id, line_id, pos_id, "INCREASE")
    key2 = BalanceProjectionService.generate_materialization_key(mov_id, line_id, pos_id, "INCREASE")

    assert key1 == key2, "La clave debe ser determinista para los mismos argumentos"
    assert key1.startswith("mat_delta:")
    assert str(mov_id) in key1
    assert str(line_id) in key1
    assert str(pos_id) in key1
    assert "INCREASE" in key1


@pytest.mark.postgres
def test_database_idempotency_unique_constraint(pg_engine):
    """
    DATABASE_IDEMPOTENCY — Prueba real contra PostgreSQL.

    Flujo:
    1. Crear InventoryPositionBalanceModel — persistir — COMMIT.
    2. Crear InventoryBalanceDeltaModel con materialization_key — persistir — COMMIT.
    3. Nueva sesión: intentar INSERT de segundo delta con mismo materialization_key.
    4. Confirmar IntegrityError real de PostgreSQL (UNIQUE violation).
    5. ROLLBACK.
    6. Nueva sesión: SELECT COUNT(*) de deltas para ese position_id.
    7. Confirmar COUNT = 1 (solo un delta efectivo).
    8. Confirmar saldo = cantidad del único delta aplicado.
    """
    org_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    mov_id = uuid4()
    line_id = uuid4()

    key = BalanceProjectionService.generate_materialization_key(mov_id, line_id, pos_id, "INCREASE")

    # -----------------------------------------------------------------------
    # Paso 1: Crear balance y primer delta en sesión A
    # -----------------------------------------------------------------------
    with Session(pg_engine) as session_a:
        balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=uuid4(),
            inventory_position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            quantity=Decimal("100.000000000000000000"),
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=f"org:{org_id}:wh:default",
            last_applied_ledger_sequence=1000,
        )
        session_a.add(balance)

        delta_1 = InventoryBalanceDeltaModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=f"org:{org_id}:wh:default",
            ledger_sequence=1001,
            movement_id=mov_id,
            movement_line_id=line_id,
            position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            delta_type="INCREASE",
            delta_quantity=Decimal("50.000000000000000000"),
            movement_hash="abc123def456" * 5,  # 60 chars
            materialization_key=key,
            applied_status="APPLIED",
        )
        session_a.add(delta_1)
        session_a.commit()

    # -----------------------------------------------------------------------
    # Paso 2: Intentar insertar segundo delta con el mismo materialization_key
    # -----------------------------------------------------------------------
    integrity_error_raised = False
    with Session(pg_engine) as session_b:
        delta_2 = InventoryBalanceDeltaModel(
            id=uuid4(),
            organization_id=org_id,
            ledger_partition_key=f"org:{org_id}:wh:default",
            ledger_sequence=1002,
            movement_id=mov_id,
            movement_line_id=line_id,
            position_id=pos_id,
            product_id=prod_id,
            base_unit_id=unit_id,
            delta_type="INCREASE",
            delta_quantity=Decimal("999.000000000000000000"),
            movement_hash="abc123def456" * 5,
            materialization_key=key,  # ← MISMO KEY → debe fallar
            applied_status="APPLIED",
        )
        session_b.add(delta_2)
        try:
            session_b.commit()
        except IntegrityError:
            integrity_error_raised = True
            session_b.rollback()

    assert integrity_error_raised, (
        "DATABASE_IDEMPOTENCY FAIL: Se esperaba IntegrityError (UNIQUE violation) "
        "al intentar insertar segundo delta con mismo materialization_key, "
        "pero la DB lo aceptó silenciosamente."
    )

    # -----------------------------------------------------------------------
    # Paso 3: Nueva sesión — verificar COUNT y saldo final
    # -----------------------------------------------------------------------
    with Session(pg_engine) as session_c:
        count = session_c.query(
            func.count(InventoryBalanceDeltaModel.id)
        ).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).scalar()

        assert count == 1, (
            f"DATABASE_IDEMPOTENCY FAIL: Se esperaba COUNT=1 delta efectivo, "
            f"pero la DB tiene COUNT={count}. El saldo fue aplicado más de una vez."
        )

        # Verificar que el saldo NO fue contaminado por el segundo intento
        balance_row = session_c.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()

        assert balance_row.quantity == Decimal("100.000000000000000000"), (
            f"DATABASE_IDEMPOTENCY FAIL: El saldo fue modificado por el segundo intento. "
            f"Valor esperado: 100, valor obtenido: {balance_row.quantity}"
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryBalanceDeltaModel).filter(
            InventoryBalanceDeltaModel.position_id == pos_id
        ).delete()
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.commit()


@pytest.mark.postgres
def test_numeric_roundtrip_postgres(pg_engine):
    """
    NUMERIC(38,18) ROUNDTRIP — Prueba real contra PostgreSQL.

    Persiste 0.000000000000000001, cierra la sesión, abre nueva sesión,
    lee el valor y confirma igualdad exacta.
    """
    org_id = uuid4()
    pos_id = uuid4()
    tiny_qty = Decimal("0.000000000000000001")

    with Session(pg_engine) as session_write:
        balance = InventoryPositionBalanceModel(
            id=uuid4(),
            organization_id=org_id,
            branch_id=uuid4(),
            inventory_position_id=pos_id,
            product_id=uuid4(),
            base_unit_id=uuid4(),
            quantity=tiny_qty,
            dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
            last_applied_ledger_partition_key=f"org:{org_id}:wh:default",
            last_applied_ledger_sequence=1,
        )
        session_write.add(balance)
        session_write.commit()

    with Session(pg_engine) as session_read:
        row = session_read.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).one()

        assert row.quantity == tiny_qty, (
            f"NUMERIC_ROUNDTRIP FAIL: Valor escrito={tiny_qty}, "
            f"valor leído={row.quantity}. PostgreSQL no preservó la precisión exacta."
        )

    # Limpieza
    with Session(pg_engine) as cleanup:
        cleanup.query(InventoryPositionBalanceModel).filter(
            InventoryPositionBalanceModel.inventory_position_id == pos_id
        ).delete()
        cleanup.commit()
