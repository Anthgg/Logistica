from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ...domain.enums import DifferenceType
from ...domain.errors import reception_difference_error


class ReceptionDifferenceQuantityService:
    @staticmethod
    def calculate_difference(expected_quantity: Decimal, observed_quantity: Decimal, difference_type: str) -> dict:
        expected = Decimal(str(expected_quantity))
        observed = Decimal(str(observed_quantity))
        diff = expected - observed
        abs_diff = abs(diff)

        return {
            "expected_quantity": expected,
            "observed_quantity": observed,
            "difference_quantity": diff,
            "absolute_difference": abs_diff,
            "difference_type": difference_type,
            "is_shortage": diff > 0,
            "is_overage": diff < 0,
        }

    @staticmethod
    def calculate_variance_percentage(expected_base: Decimal, observed_base: Decimal) -> Decimal:
        expected = Decimal(str(expected_base))
        observed = Decimal(str(observed_base))
        if expected == 0:
            raise reception_difference_error("ReceptionDifferenceQuantityInvalid", "La cantidad esperada base no puede ser cero para calcular el porcentaje de varianza.")
        variance = ((observed - expected) / expected) * Decimal("100")
        return variance.quantize(Decimal("0.01"))
