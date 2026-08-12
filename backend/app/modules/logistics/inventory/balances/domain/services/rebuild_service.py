from decimal import Decimal
from typing import Any, Dict, List


class RebuildService:
    """Servicio de reconstrucción (rebuild) total o parcial de saldos mediante replay ordenado del ledger MOV.
    
    Adhiere al principio:
    MOVIMIENTO -> Replay -> Nueva proyección temporal -> Verificación -> Swap atómico.
    """

    def replay_movements_and_calculate(
        self, movement_lines: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """Calcula el saldo acumulado procesando secuencialmente cada línea del ledger MOV en orden ascendente."""
        balances: Dict[str, Decimal] = {}
        for line in movement_lines:
            position_id = str(line["position_id"])
            qty = Decimal(str(line["quantity"]))
            direction = str(line.get("direction", "INCREASE")).upper()

            current = balances.get(position_id, Decimal("0.000000000000000000"))
            if direction == "INCREASE":
                balances[position_id] = current + qty
            elif direction == "DECREASE":
                balances[position_id] = current - qty
            else:
                raise ValueError(f"Invalid movement line direction: {direction}. Only INCREASE or DECREASE are permitted.")
        return balances
