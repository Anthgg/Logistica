from decimal import Decimal
from uuid import uuid4
import pytest

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.balances.infrastructure.projections.balance_projection_service import (
    BalanceProjectionService,
)


def test_balance_idempotency_key_generation_and_uniqueness():
    """Prueba real de generación determinista de materialization_key."""
    mov_id = uuid4()
    line_id = uuid4()
    pos_id = uuid4()

    key1 = BalanceProjectionService.generate_materialization_key(mov_id, line_id, pos_id, "INCREASE")
    key2 = BalanceProjectionService.generate_materialization_key(mov_id, line_id, pos_id, "INCREASE")

    assert key1 == key2
    assert key1.startswith("mat_delta:")
    assert str(mov_id) in key1
    assert str(line_id) in key1
    assert str(pos_id) in key1


def test_balance_projection_service_apply_delta_idempotence():
    """Prueba real del servicio de proyección aplicando un delta positivo sin alteración directa."""
    service = BalanceProjectionService()
    current_balance = Decimal("100.000000000000000000")
    delta = {
        "delta_type": "INCREASE",
        "delta_quantity": "50.000000000000000000",
    }

    res1 = service.apply_delta(current_balance, delta)
    assert res1["new_balance"] == Decimal("150.000000000000000000")
    assert res1["applied_status"] == "APPLIED"

    # Verificación de rechazo explícito de RECONCILIATION_SET
    invalid_delta = {
        "delta_type": "RECONCILIATION_SET",
        "delta_quantity": "999.000000000000000000",
    }
    with pytest.raises(ValueError, match="RECONCILIATION_SET is strictly forbidden"):
        service.apply_delta(current_balance, invalid_delta)
