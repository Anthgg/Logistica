"""Quantity comparison service for Phase 024."""

from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.units.models import UnitOfMeasureModel
from app.modules.logistics.units.path_resolver import ConversionPathResolver


class QuantityComparisonService:
    """Compares two quantities across units using Decimal arithmetic."""

    def __init__(self, db: Session):
        self.db = db
        self.resolver = ConversionPathResolver(db)

    def compare(
        self,
        left_quantity: Decimal,
        left_unit_code: str,
        right_quantity: Decimal,
        right_unit_code: str,
        product_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        stmt_l = select(UnitOfMeasureModel).where(UnitOfMeasureModel.normalized_code == left_unit_code.upper())
        stmt_r = select(UnitOfMeasureModel).where(UnitOfMeasureModel.normalized_code == right_unit_code.upper())

        u_left = self.db.scalar(stmt_l)
        u_right = self.db.scalar(stmt_r)

        if not u_left or not u_right:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Left or right unit of measure not found.")

        # Convert right unit quantity to left unit
        factor_r_to_l, path, _ = self.resolver.resolve_path(
            source_unit_id=u_right.id,
            target_unit_id=u_left.id,
            organization_id=organization_id,
            product_id=product_id,
        )

        right_converted = right_quantity * factor_r_to_l
        diff = left_quantity - right_converted

        if abs(diff) < Decimal("0.000001"):
            comparison = "EQUAL"
        elif left_quantity > right_converted:
            comparison = "GREATER_THAN"
        else:
            comparison = "LESS_THAN"

        return {
            "left": {"quantity": str(left_quantity), "unit": left_unit_code},
            "right": {"quantity": str(right_quantity), "unit": right_unit_code},
            "comparison": comparison,
            "right_converted_to_left": str(right_converted),
            "difference": str(diff),
            "equivalent": comparison == "EQUAL",
            "conversion_path": path,
        }
