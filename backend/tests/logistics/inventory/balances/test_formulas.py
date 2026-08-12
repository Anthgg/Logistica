"""
test_formulas.py — Tests UNITARIOS de fórmulas de saldos (Fase 045)

Clasificación: UNIT_TEST
- Sin DB, sin infraestructura real
- Validan la lógica de cálculo de Physical, ATP, Quarantine
"""
import pytest
from decimal import Decimal

pytestmark = pytest.mark.unit

from app.modules.logistics.inventory.balances.domain.services.formula_service import (
    InventoryBalanceFormulaService,
)


def test_calculate_physical_on_hand():
    positions = [
        {"quantity": "100.000000000000000000", "transit_state": "NOT_IN_TRANSIT"},
        {"quantity": "50.000000000000000000", "transit_state": "IN_TRANSIT_INTER_WAREHOUSE"},
    ]
    result = InventoryBalanceFormulaService.calculate_physical_on_hand(positions)
    assert result == Decimal("100.000000000000000000")


def test_calculate_available_to_promise():
    positions = [
        {
            "quantity": "200.000000000000000000",
            "availability_state": "AVAILABLE",
            "quality_state": "APPROVED",
            "transit_state": "NOT_IN_TRANSIT",
            "damage_state": "NORMAL",
        },
        {
            "quantity": "30.000000000000000000",
            "availability_state": "QUARANTINE",
            "quality_state": "QUARANTINED",
            "transit_state": "NOT_IN_TRANSIT",
            "damage_state": "NORMAL",
        },
    ]
    result = InventoryBalanceFormulaService.calculate_available_to_promise(positions)
    assert result == Decimal("200.000000000000000000")


def test_calculate_quarantine_stock():
    positions = [
        {"quantity": "40.000000000000000000", "quality_state": "QUARANTINED"},
        {"quantity": "10.000000000000000000", "availability_state": "QUARANTINE"},
    ]
    result = InventoryBalanceFormulaService.calculate_quarantine_stock(positions)
    assert result == Decimal("50.000000000000000000")
