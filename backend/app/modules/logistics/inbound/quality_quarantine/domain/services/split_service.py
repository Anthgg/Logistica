"""Phase 042 — Inventory disposition split service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    InboundInventoryAllocationSplitInvalid,
)


def validate_split(
    *,
    original_quantity: Decimal,
    original_base_quantity: Decimal,
    first_child_quantity: Decimal,
    first_child_base_quantity: Decimal,
    second_child_quantity: Decimal,
    second_child_base_quantity: Decimal,
) -> None:
    """Validate that a split produces exact halves that sum to original."""
    eps = Decimal("0.000000000000000001")

    if first_child_quantity <= 0 or second_child_quantity <= 0:
        raise InboundInventoryAllocationSplitInvalid(
            child_sum=str(first_child_quantity + second_child_quantity),
            original=str(original_quantity),
        )

    if first_child_base_quantity <= 0 or second_child_base_quantity <= 0:
        raise InboundInventoryAllocationSplitInvalid(
            child_sum=str(first_child_base_quantity + second_child_base_quantity),
            original=str(original_base_quantity),
        )

    child_sum = first_child_quantity + second_child_quantity
    if abs(child_sum - original_quantity) > eps:
        raise InboundInventoryAllocationSplitInvalid(
            child_sum=str(child_sum),
            original=str(original_quantity),
        )

    child_base_sum = first_child_base_quantity + second_child_base_quantity
    if abs(child_base_sum - original_base_quantity) > eps:
        raise InboundInventoryAllocationSplitInvalid(
            child_sum=str(child_base_sum),
            original=str(original_base_quantity),
        )
