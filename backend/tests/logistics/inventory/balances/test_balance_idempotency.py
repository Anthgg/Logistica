from decimal import Decimal

import pytest

from app.modules.logistics.inventory.balances.infrastructure.projections.balance_projection_service import (
    BalanceProjectionService,
)


def test_materialization_key_generation():
    key1 = BalanceProjectionService.generate_materialization_key(
        movement_id="mov-100",
        movement_line_id="line-1",
        position_id="pos-5",
        delta_direction="INCREASE",
    )
    key2 = BalanceProjectionService.generate_materialization_key(
        movement_id="mov-100",
        movement_line_id="line-1",
        position_id="pos-5",
        delta_direction="INCREASE",
    )
    assert key1 == key2
    assert key1 == "mat_delta:mov-100:line-1:pos-5:INCREASE"


def test_reconciliation_set_strictly_forbidden():
    projection_service = BalanceProjectionService()
    delta = {
        "delta_type": "RECONCILIATION_SET",
        "delta_quantity": "100.000000000000000000",
    }
    with pytest.raises(ValueError, match="RECONCILIATION_SET is strictly forbidden"):
        projection_service.apply_delta(Decimal("50.000000000000000000"), delta)
