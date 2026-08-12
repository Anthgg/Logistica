"""PurchaseOrderMoneyService — exact Decimal monetary calculations for POs.

Rules:
- Never uses float. All arithmetic uses Decimal with ROUND_HALF_UP.
- Returns a MonetarySummary dataclass, not primitive types.
- Validates integrity: recalculated totals must match stored totals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Sequence

from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderMonetaryCalculationMismatch,
    PurchaseOrderDiscountInvalid,
    PurchaseOrderChargeInvalid,
    PurchaseOrderTaxInvalid,
)
from app.modules.logistics.procurement.purchase_orders.domain.value_objects.money import Money

_ZERO = Decimal("0")


@dataclass(frozen=True)
class LineSummary:
    """Result of calculating a single line's monetary values."""
    line_number: int
    ordered_quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    freight_amount: Decimal
    other_charges_amount: Decimal
    line_subtotal: Decimal       # ordered_quantity * unit_price
    line_net: Decimal            # line_subtotal - discount_amount
    line_total: Decimal          # line_net + tax_amount + freight_amount + other_charges_amount
    currency_code: str


@dataclass
class MonetarySummary:
    """Aggregate monetary summary for an entire purchase order revision."""
    currency_code: str
    line_summaries: list[LineSummary] = field(default_factory=list)

    # Header-level aggregates
    subtotal: Decimal = _ZERO                # sum of (qty * unit_price) before discounts
    discount_total: Decimal = _ZERO          # sum of all line discounts
    net_subtotal: Decimal = _ZERO            # subtotal - discount_total
    tax_total: Decimal = _ZERO               # sum of all tax amounts
    freight_total: Decimal = _ZERO           # sum of all freight amounts
    other_charges_total: Decimal = _ZERO     # sum of other charges
    grand_total: Decimal = _ZERO             # net_subtotal + tax_total + freight_total + other_charges_total

    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "subtotal": str(self.subtotal),
            "discount_total": str(self.discount_total),
            "net_subtotal": str(self.net_subtotal),
            "tax_total": str(self.tax_total),
            "freight_total": str(self.freight_total),
            "other_charges_total": str(self.other_charges_total),
            "grand_total": str(self.grand_total),
        }


@dataclass(frozen=True)
class LineInput:
    """Input for a single PO line monetary calculation."""
    line_number: int
    ordered_quantity: Decimal
    unit_price: Decimal
    currency_code: str
    discount_type: str | None = None        # PERCENTAGE | FIXED_AMOUNT | NONE
    discount_value: Decimal | None = None
    tax_rate: Decimal | None = None          # as percentage 0-100
    tax_amount_override: Decimal | None = None  # use if tax is pre-computed
    freight_amount: Decimal = _ZERO
    other_charges_amount: Decimal = _ZERO


class PurchaseOrderMoneyService:
    """Exact Decimal monetary calculation service for purchase orders.

    All methods are pure functions — no side effects, no database access.
    The caller is responsible for persisting the results.
    """

    ROUNDING = ROUND_HALF_UP

    def __init__(self, scale: int = 2) -> None:
        if scale < 0 or scale > 10:
            raise ValueError(f"scale must be 0-10, got {scale}")
        self._scale = scale
        self._quantum = Decimal(10) ** -scale

    def _q(self, value: Decimal) -> Decimal:
        """Quantize a Decimal to the configured scale."""
        return value.quantize(self._quantum, rounding=self.ROUNDING)

    def calculate_line(self, line: LineInput) -> LineSummary:
        """Calculate the monetary values for a single PO line."""
        self._validate_line_input(line)

        qty = line.ordered_quantity
        price = line.unit_price

        # Subtotal
        line_subtotal = self._q(qty * price)

        # Discount
        discount_amount = self._resolve_discount(
            line_subtotal,
            line.discount_type,
            line.discount_value,
        )

        # Net after discount
        line_net = self._q(line_subtotal - discount_amount)
        if line_net < _ZERO:
            raise PurchaseOrderDiscountInvalid(
                f"Line {line.line_number}: discount amount {discount_amount} "
                f"exceeds line subtotal {line_subtotal}."
            )

        # Tax
        tax_amount = self._resolve_tax(
            line_net,
            line.tax_rate,
            line.tax_amount_override,
        )

        # Freight and other charges
        freight_amount = self._q(line.freight_amount)
        other_charges = self._q(line.other_charges_amount)

        # Total
        line_total = self._q(line_net + tax_amount + freight_amount + other_charges)

        return LineSummary(
            line_number=line.line_number,
            ordered_quantity=qty,
            unit_price=price,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            freight_amount=freight_amount,
            other_charges_amount=other_charges,
            line_subtotal=line_subtotal,
            line_net=line_net,
            line_total=line_total,
            currency_code=line.currency_code,
        )

    def calculate_summary(self, lines: Sequence[LineInput]) -> MonetarySummary:
        """Calculate the aggregate monetary summary for all PO lines."""
        if not lines:
            raise ValueError("Cannot calculate summary for empty line list.")

        # All lines must share the same currency
        currencies = {line.currency_code for line in lines}
        if len(currencies) > 1:
            raise PurchaseOrderMonetaryCalculationMismatch(
                f"All lines must share the same currency. Found: {currencies}"
            )

        currency_code = next(iter(currencies))
        line_summaries: list[LineSummary] = []

        subtotal = _ZERO
        discount_total = _ZERO
        tax_total = _ZERO
        freight_total = _ZERO
        other_charges_total = _ZERO

        for line in lines:
            summary = self.calculate_line(line)
            line_summaries.append(summary)
            subtotal = self._q(subtotal + summary.line_subtotal)
            discount_total = self._q(discount_total + summary.discount_amount)
            tax_total = self._q(tax_total + summary.tax_amount)
            freight_total = self._q(freight_total + summary.freight_amount)
            other_charges_total = self._q(other_charges_total + summary.other_charges_amount)

        net_subtotal = self._q(subtotal - discount_total)
        grand_total = self._q(net_subtotal + tax_total + freight_total + other_charges_total)

        return MonetarySummary(
            currency_code=currency_code,
            line_summaries=line_summaries,
            subtotal=subtotal,
            discount_total=discount_total,
            net_subtotal=net_subtotal,
            tax_total=tax_total,
            freight_total=freight_total,
            other_charges_total=other_charges_total,
            grand_total=grand_total,
        )

    def verify_integrity(
        self,
        summary: MonetarySummary,
        stored_grand_total: Decimal,
        tolerance: Decimal = Decimal("0.01"),
    ) -> bool:
        """Verify that the recalculated grand_total matches the stored value.

        Returns True if within tolerance, raises otherwise.
        Tolerance is provided for legacy rounding compatibility only.
        """
        diff = abs(summary.grand_total - stored_grand_total)
        if diff > tolerance:
            raise PurchaseOrderMonetaryCalculationMismatch(
                f"Monetary integrity check failed: recalculated grand_total="
                f"{summary.grand_total} differs from stored={stored_grand_total} "
                f"by {diff} (tolerance={tolerance})."
            )
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_line_input(self, line: LineInput) -> None:
        if isinstance(line.ordered_quantity, float) or isinstance(line.unit_price, float):
            raise TypeError(
                f"Line {line.line_number}: float values are not allowed. Use Decimal."
            )
        if line.ordered_quantity <= _ZERO:
            raise ValueError(f"Line {line.line_number}: ordered_quantity must be positive.")
        if line.unit_price < _ZERO:
            raise ValueError(f"Line {line.line_number}: unit_price cannot be negative.")
        if line.freight_amount < _ZERO:
            raise PurchaseOrderChargeInvalid(
                f"Line {line.line_number}: freight_amount cannot be negative."
            )
        if line.other_charges_amount < _ZERO:
            raise PurchaseOrderChargeInvalid(
                f"Line {line.line_number}: other_charges_amount cannot be negative."
            )

    def _resolve_discount(
        self,
        line_subtotal: Decimal,
        discount_type: str | None,
        discount_value: Decimal | None,
    ) -> Decimal:
        if not discount_type or discount_type in ("NONE", "NO_DISCOUNT"):
            return _ZERO
        if discount_value is None:
            raise PurchaseOrderDiscountInvalid(
                f"discount_type={discount_type!r} requires a discount_value."
            )
        if isinstance(discount_value, float):
            raise TypeError("discount_value must be Decimal, not float.")
        if discount_value < _ZERO:
            raise PurchaseOrderDiscountInvalid("discount_value cannot be negative.")

        if discount_type == "PERCENTAGE":
            if discount_value > Decimal("100"):
                raise PurchaseOrderDiscountInvalid("Discount percentage cannot exceed 100%.")
            return self._q(line_subtotal * discount_value / Decimal("100"))
        elif discount_type == "FIXED_AMOUNT":
            return self._q(discount_value)
        else:
            raise PurchaseOrderDiscountInvalid(
                f"Unknown discount_type: {discount_type!r}. "
                "Expected: PERCENTAGE, FIXED_AMOUNT, NONE."
            )

    def _resolve_tax(
        self,
        taxable_base: Decimal,
        tax_rate: Decimal | None,
        tax_amount_override: Decimal | None,
    ) -> Decimal:
        if tax_amount_override is not None:
            if isinstance(tax_amount_override, float):
                raise TypeError("tax_amount_override must be Decimal, not float.")
            if tax_amount_override < _ZERO:
                raise PurchaseOrderTaxInvalid("tax_amount_override cannot be negative.")
            return self._q(tax_amount_override)

        if tax_rate is None:
            return _ZERO

        if isinstance(tax_rate, float):
            raise TypeError("tax_rate must be Decimal, not float.")
        if tax_rate < _ZERO:
            raise PurchaseOrderTaxInvalid("tax_rate cannot be negative.")
        if tax_rate > Decimal("100"):
            raise PurchaseOrderTaxInvalid("tax_rate cannot exceed 100%.")

        return self._q(taxable_base * tax_rate / Decimal("100"))
