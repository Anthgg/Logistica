from decimal import Decimal
from typing import Any

from app.modules.logistics.inventory.balances.domain.services.formula_service import (
    InventoryBalanceFormulaService,
)


class InventoryBalanceAvailabilityProvider:
    """Proveedor unificado de disponibilidad operativa y métricas de saldos de inventario."""

    def __init__(self, formula_service: InventoryBalanceFormulaService | None = None):
        self.formula_service = formula_service or InventoryBalanceFormulaService()

    def get_summary_metrics(self, position_balances: list[dict[str, Any]]) -> dict[str, Decimal]:
        """Calcula el resumen completo de saldos para las posiciones especificadas."""
        return {
            "physical_on_hand": self.formula_service.calculate_physical_on_hand(position_balances),
            "available_to_promise": self.formula_service.calculate_available_to_promise(position_balances),
            "quarantine_stock": self.formula_service.calculate_quarantine_stock(position_balances),
            "blocked_stock": self.formula_service.calculate_blocked_stock(position_balances),
            "in_transit_stock": self.formula_service.calculate_in_transit_stock(position_balances),
        }
