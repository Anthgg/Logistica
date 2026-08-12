from decimal import Decimal


class NegativeStockPolicy:
    """Política de control de stock negativo (DENY por defecto)."""

    def __init__(self, allow_negative: bool = False):
        self.allow_negative = allow_negative

    def validate(self, current_balance: Decimal, delta_quantity: Decimal) -> None:
        new_balance = current_balance + delta_quantity
        if not self.allow_negative and new_balance < Decimal("0"):
            raise ValueError(
                f"Negative stock policy violation: Resulting balance {new_balance} is below zero. "
                f"Current balance: {current_balance}, requested delta: {delta_quantity}."
            )
