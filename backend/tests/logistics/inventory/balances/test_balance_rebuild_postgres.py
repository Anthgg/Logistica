from decimal import Decimal
import pytest

from app.modules.logistics.inventory.balances.domain.services.rebuild_service import (
    RebuildService,
)


def test_rebuild_service_replay_calculation():
    """Valida la reconstrucción determinista de saldos mediante replay de líneas del ledger (+100, -30, +20 = 90)."""
    service = RebuildService()
    lines = [
        {"position_id": "pos-1", "quantity": "100.000000000000000000", "direction": "INCREASE"},
        {"position_id": "pos-1", "quantity": "30.000000000000000000", "direction": "DECREASE"},
        {"position_id": "pos-1", "quantity": "20.000000000000000000", "direction": "INCREASE"},
    ]

    calculated = service.replay_movements_and_calculate(lines)
    assert calculated["pos-1"] == Decimal("90.000000000000000000")


def test_rebuild_service_determinism():
    """Valida que ejecutar el rebuild dos veces produzca exactamente los mismos saldos."""
    service = RebuildService()
    lines = [
        {"position_id": "pos-1", "quantity": "50.000000000000000000", "direction": "INCREASE"},
        {"position_id": "pos-1", "quantity": "10.000000000000000000", "direction": "DECREASE"},
    ]

    res1 = service.replay_movements_and_calculate(lines)
    res2 = service.replay_movements_and_calculate(lines)

    assert res1 == res2
    assert res1["pos-1"] == Decimal("40.000000000000000000")
