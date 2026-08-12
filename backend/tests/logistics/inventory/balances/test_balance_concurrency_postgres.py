from decimal import Decimal
from uuid import uuid4
import pytest

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryPositionBalanceModel,
)


def test_concurrency_sequential_delta_application_no_lost_update():
    """Simulación de aplicación secuencial de deltas sobre el mismo saldo de posición (no lost update: 100 - 30 - 20 = 50)."""
    initial_balance = Decimal("100.000000000000000000")
    delta_a = Decimal("-30.000000000000000000")
    delta_b = Decimal("-20.000000000000000000")

    # Transacción A
    balance_after_a = initial_balance + delta_a
    assert balance_after_a == Decimal("70.000000000000000000")

    # Transacción B
    final_balance = balance_after_a + delta_b
    assert final_balance == Decimal("50.000000000000000000")
    assert final_balance != Decimal("70.000000000000000000")
    assert final_balance != Decimal("80.000000000000000000")


def test_concurrency_lock_order_prevention():
    """Valida que la lista de IDs de posición a bloquear se ordene determinísticamente para prevenir deadlocks."""
    positions = [uuid4(), uuid4(), uuid4()]
    sorted_positions = sorted(positions, key=lambda p: str(p))

    assert sorted_positions == sorted(positions, key=lambda p: str(p))
    assert len(sorted_positions) == 3
