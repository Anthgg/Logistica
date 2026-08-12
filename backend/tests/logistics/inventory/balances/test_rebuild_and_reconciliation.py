from decimal import Decimal

from app.modules.logistics.inventory.balances.domain.services.rebuild_service import (
    RebuildService,
)
from app.modules.logistics.inventory.balances.domain.services.reconciliation_service import (
    ReconciliationService,
)


def test_rebuild_service_replay():
    lines = [
        {"position_id": "pos_1", "quantity": "100.000000000000000000", "direction": "INCREASE"},
        {"position_id": "pos_1", "quantity": "30.000000000000000000", "direction": "DECREASE"},
        {"position_id": "pos_2", "quantity": "50.000000000000000000", "direction": "INCREASE"},
    ]
    rebuilder = RebuildService()
    balances = rebuilder.replay_movements_and_calculate(lines)

    assert balances["pos_1"] == Decimal("70.000000000000000000")
    assert balances["pos_2"] == Decimal("50.000000000000000000")


def test_reconciliation_service_detect_diff():
    projected = {
        "pos_1": Decimal("70.000000000000000000"),
        "pos_2": Decimal("60.000000000000000000"),  # Inconsistencia voluntaria
    }
    replayed = {
        "pos_1": Decimal("70.000000000000000000"),
        "pos_2": Decimal("50.000000000000000000"),
    }
    reconciler = ReconciliationService()
    diffs = reconciler.reconcile(projected, replayed)

    assert len(diffs) == 1
    assert diffs[0]["position_id"] == "pos_2"
    assert diffs[0]["difference_quantity"] == Decimal("10.000000000000000000")
