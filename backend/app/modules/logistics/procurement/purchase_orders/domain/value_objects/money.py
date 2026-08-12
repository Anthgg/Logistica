"""Domain value objects for Phase 034 — Purchase Orders.

Rules:
- All monetary amounts use Decimal. Never float.
- Money objects are immutable.
- Currency codes must be 3-character ISO 4217.
- Quantities must be positive Decimal values.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import ClassVar

_ISO_4217_PATTERN = re.compile(r"^[A-Z]{3}$")
_PO_CODE_PATTERN = re.compile(r"^OC-[A-Z0-9]{2,10}-\d{4}-\d{6}$")


class Money:
    """Immutable monetary value with ISO 4217 currency."""

    ZERO: ClassVar["Money"]

    __slots__ = ("_amount", "_currency_code", "_scale")

    def __init__(
        self,
        amount: Decimal | str | int,
        currency_code: str,
        scale: int = 2,
    ) -> None:
        if isinstance(amount, float):
            raise TypeError("Money does not accept float. Use Decimal or str.")
        try:
            d = Decimal(str(amount))
        except InvalidOperation as exc:
            raise ValueError(f"Invalid monetary amount: {amount!r}") from exc

        if d.is_nan() or d.is_infinite():
            raise ValueError(f"Money amount cannot be NaN or Infinite: {amount!r}")

        if not _ISO_4217_PATTERN.match(currency_code.upper()):
            raise ValueError(f"Invalid ISO 4217 currency code: {currency_code!r}")

        quantum = Decimal(10) ** -scale
        self._amount = d.quantize(quantum, rounding=ROUND_HALF_UP)
        self._currency_code = currency_code.upper()
        self._scale = scale

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @property
    def scale(self) -> int:
        return self._scale

    def add(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self._amount + other._amount, self._currency_code, self._scale)

    def subtract(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self._amount - other._amount, self._currency_code, self._scale)

    def multiply(self, factor: Decimal | str | int) -> "Money":
        if isinstance(factor, float):
            raise TypeError("Money.multiply does not accept float.")
        f = Decimal(str(factor))
        return Money(self._amount * f, self._currency_code, self._scale)

    def is_zero(self) -> bool:
        return self._amount == Decimal("0")

    def is_negative(self) -> bool:
        return self._amount < Decimal("0")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount == other._amount and self._currency_code == other._currency_code

    def __repr__(self) -> str:
        return f"Money({self._amount}, {self._currency_code!r})"

    def _assert_same_currency(self, other: "Money") -> None:
        if self._currency_code != other._currency_code:
            raise ValueError(
                f"Cannot mix currencies: {self._currency_code} and {other._currency_code}"
            )

    @classmethod
    def zero(cls, currency_code: str, scale: int = 2) -> "Money":
        return cls(Decimal("0"), currency_code, scale)

    def to_dict(self) -> dict:
        return {"amount": str(self._amount), "currency_code": self._currency_code}


Money.ZERO = Money(Decimal("0"), "PEN")  # type: ignore[assignment]


class QuantityAmount:
    """Immutable positive decimal quantity with a unit code."""

    __slots__ = ("_value", "_unit_code")

    def __init__(self, value: Decimal | str | int, unit_code: str) -> None:
        if isinstance(value, float):
            raise TypeError("QuantityAmount does not accept float.")
        try:
            d = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"Invalid quantity: {value!r}") from exc

        if d.is_nan() or d.is_infinite():
            raise ValueError(f"Quantity cannot be NaN or Infinite: {value!r}")
        if d <= Decimal("0"):
            raise ValueError(f"Quantity must be positive. Got: {d}")

        self._value = d
        self._unit_code = unit_code.strip().upper()

    @property
    def value(self) -> Decimal:
        return self._value

    @property
    def unit_code(self) -> str:
        return self._unit_code

    def add(self, other: "QuantityAmount") -> "QuantityAmount":
        if self._unit_code != other._unit_code:
            raise ValueError(
                f"Cannot add quantities with different units: {self._unit_code} and {other._unit_code}"
            )
        return QuantityAmount(self._value + other._value, self._unit_code)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QuantityAmount):
            return NotImplemented
        return self._value == other._value and self._unit_code == other._unit_code

    def __repr__(self) -> str:
        return f"QuantityAmount({self._value}, {self._unit_code!r})"

    def to_dict(self) -> dict:
        return {"value": str(self._value), "unit_code": self._unit_code}


class PurchaseOrderCode:
    """Value object for a validated OC code.

    Format: OC-{BRANCH_CODE}-{YEAR}-{SEQUENCE:06d}
    Example: OC-LIM-2026-000001
    """

    __slots__ = ("_code",)

    def __init__(self, code: str) -> None:
        normalized = code.strip().upper()
        if not _PO_CODE_PATTERN.match(normalized):
            raise ValueError(
                f"Invalid purchase order code format: {code!r}. "
                "Expected: OC-{BRANCH}-{YEAR}-{6-digit-seq}"
            )
        self._code = normalized

    @property
    def value(self) -> str:
        return self._code

    @property
    def normalized(self) -> str:
        return self._code.replace("-", "").upper()

    @classmethod
    def build(cls, branch_code: str, year: int, sequence: int) -> "PurchaseOrderCode":
        """Build a code from components without constructing the full string first."""
        branch = branch_code.strip().upper()
        if not branch or len(branch) > 10:
            raise ValueError(f"Branch code must be 1-10 chars: {branch_code!r}")
        if sequence < 1:
            raise ValueError(f"Sequence must be positive: {sequence}")
        return cls(f"OC-{branch}-{year}-{sequence:06d}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PurchaseOrderCode):
            return NotImplemented
        return self._code == other._code

    def __str__(self) -> str:
        return self._code

    def __repr__(self) -> str:
        return f"PurchaseOrderCode({self._code!r})"
