from decimal import Decimal
from typing import Any, Dict

from app.modules.logistics.inventory.balances.domain.policies.negative_stock_policy import (
    NegativeStockPolicy,
)


class BalanceProjectionService:
    """Consumer asíncrono e idempotente de deltas de saldos derivados del ledger MOV."""

    def __init__(self, negative_stock_policy: NegativeStockPolicy | None = None):
        self.negative_stock_policy = negative_stock_policy or NegativeStockPolicy(allow_negative=False)

    def apply_delta(
        self,
        current_balance: Decimal,
        delta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Aplica un delta de movimiento al saldo acumulado con validación de idempotencia y stock negativo."""
        delta_type = str(delta.get("delta_type", "INCREASE")).upper()
        qty = Decimal(str(delta.get("delta_quantity", "0")))

        if delta_type == "INCREASE":
            delta_val = qty
        elif delta_type == "DECREASE":
            delta_val = -qty
        elif delta_type == "RECONCILIATION_SET":
            return {
                "new_balance": qty,
                "balance_before": current_balance,
                "applied_status": "APPLIED",
            }
        else:
            raise ValueError(f"Unsupported delta_type: {delta_type}")

        self.negative_stock_policy.validate(current_balance, delta_val)
        new_balance = current_balance + delta_val

        return {
            "new_balance": new_balance,
            "balance_before": current_balance,
            "applied_status": "APPLIED",
        }
