from decimal import Decimal
from typing import Any, Dict, List


class ReconciliationService:
    """Servicio de reconciliación y auditoría de consistencia entre la proyección materializada y el ledger."""

    def reconcile(
        self,
        projected_balances: Dict[str, Decimal],
        replayed_balances: Dict[str, Decimal],
    ) -> List[Dict[str, Any]]:
        """Compara posición por posición la proyección actual contra el cálculo replay del ledger MOV."""
        differences = []
        all_positions = set(projected_balances.keys()) | set(replayed_balances.keys())

        for pos_id in sorted(all_positions):
            proj_qty = projected_balances.get(pos_id, Decimal("0.000000000000000000"))
            repl_qty = replayed_balances.get(pos_id, Decimal("0.000000000000000000"))

            diff_qty = proj_qty - repl_qty
            if diff_qty != Decimal("0.000000000000000000"):
                differences.append(
                    {
                        "position_id": pos_id,
                        "projected_quantity": proj_qty,
                        "replayed_quantity": repl_qty,
                        "difference_quantity": diff_qty,
                        "status": "MISMATCH_DETECTED",
                    }
                )
        return differences
