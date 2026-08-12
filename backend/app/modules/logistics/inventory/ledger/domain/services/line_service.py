"""Server-side quantity normalization for inventory movement lines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementConversionMissing,
    InventoryMovementUnitInvalid,
)
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.units.models import UnitConversionRuleModel


@dataclass(frozen=True)
class DerivedLineQuantity:
    base_quantity: Decimal
    base_unit_id: UUID
    conversion_rule_id: UUID | None
    conversion_snapshot: dict | None


class InventoryMovementLineService:
    """Derive base quantity from trusted unit-conversion rules using Decimal."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def derive_base_quantity(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        unit_id: UUID,
        base_unit_id: UUID,
        conversion_rule_id: UUID | None,
    ) -> DerivedLineQuantity:
        if quantity <= Decimal("0"):
            raise InventoryMovementUnitInvalid("Quantity must be greater than zero.")

        if unit_id == base_unit_id:
            if conversion_rule_id is not None:
                raise InventoryMovementUnitInvalid(
                    "A conversion rule is not allowed when unit and base unit are equal."
                )
            return DerivedLineQuantity(quantity, base_unit_id, None, None)

        if conversion_rule_id is None:
            raise InventoryMovementConversionMissing(
                "conversion_rule_id is required when unit_id differs from base_unit_id."
            )

        rule = self._db.get(UnitConversionRuleModel, conversion_rule_id)
        now = datetime.now(timezone.utc)
        if (
            rule is None
            or rule.status != "ACTIVE"
            or rule.source_unit_id != unit_id
            or rule.target_unit_id != base_unit_id
            or (rule.organization_id is not None and rule.organization_id != organization_id)
            or (rule.product_id is not None and rule.product_id != product_id)
            or (rule.effective_from is not None and rule.effective_from > now)
            or (rule.effective_to is not None and rule.effective_to <= now)
        ):
            raise InventoryMovementConversionMissing(
                "The requested unit conversion rule is missing, inactive or out of scope."
            )

        exact = quantity * Decimal(str(rule.multiplier))
        base_quantity, rounding_applied = UnitConversionEngine.apply_rounding(
            exact,
            precision=int(rule.precision),
            policy=str(rule.rounding_policy),
        )
        snapshot = {
            "rule_id": str(rule.id),
            "version": str(rule.version),
            "content_hash": str(rule.content_hash),
            "source_unit_id": str(rule.source_unit_id),
            "target_unit_id": str(rule.target_unit_id),
            "multiplier": str(rule.multiplier),
            "precision": int(rule.precision),
            "rounding_policy": str(rule.rounding_policy),
            "rounding_applied": rounding_applied,
        }
        return DerivedLineQuantity(
            base_quantity=base_quantity,
            base_unit_id=base_unit_id,
            conversion_rule_id=rule.id,
            conversion_snapshot=snapshot,
        )
