from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.logistics.inventory.balances.domain.policies.negative_stock_policy import (
    NegativeStockPolicy,
)


class BalanceProjectionService:
    """Consumer asíncrono e idempotente de deltas de saldos derivados del ledger MOV.
    
    ESTRICTAMENTE ADHIERE A:
    - MOVIMIENTO = HECHO HISTÓRICO
    - SALDO = PROYECCIÓN MATERIALIZADA
    
    Queda expresamente PROHIBIDO el uso de RECONCILIATION_SET o métodos arbitrarios de set_stock.
    """

    def __init__(self, negative_stock_policy: NegativeStockPolicy | None = None):
        self.negative_stock_policy = negative_stock_policy or NegativeStockPolicy(allow_negative=False)

    def apply_delta(
        self,
        current_balance: Decimal,
        delta: dict[str, Any],
    ) -> dict[str, Any]:
        """Aplica un delta de movimiento (INCREASE o DECREASE) al saldo acumulado."""
        delta_type = str(delta.get("delta_type", "INCREASE")).upper()
        
        # PROHIBICIÓN ESTRICTA: RECONCILIATION_SET no es un delta válido de proyección
        if delta_type == "RECONCILIATION_SET":
            raise ValueError(
                "RECONCILIATION_SET is strictly forbidden in projection streaming. "
                "Balances cannot be set directly; reconciliations report mismatches without mutating MOV history."
            )

        qty = Decimal(str(delta.get("delta_quantity", "0")))

        if delta_type == "INCREASE":
            delta_val = qty
        elif delta_type == "DECREASE":
            delta_val = -qty
        else:
            raise ValueError(f"Unsupported delta_type: {delta_type}. Allowed types: INCREASE, DECREASE.")

        # Validar política de stock negativo (DENY por defecto)
        self.negative_stock_policy.validate(current_balance, delta_val)
        new_balance = current_balance + delta_val

        return {
            "new_balance": new_balance,
            "balance_before": current_balance,
            "applied_status": "APPLIED",
        }

    @staticmethod
    def generate_materialization_key(
        movement_id: UUID | str,
        movement_line_id: UUID | str,
        position_id: UUID | str,
        delta_direction: str,
    ) -> str:
        """Genera una clave determinista e inmutable para garantizar idempotencia DB vía UNIQUE constraint."""
        return f"mat_delta:{movement_id}:{movement_line_id}:{position_id}:{delta_direction.upper()}"
