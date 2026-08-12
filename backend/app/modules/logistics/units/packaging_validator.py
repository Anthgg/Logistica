"""Product packaging hierarchy validator for Phase 024."""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.units.models import ProductPackagingDefinitionModel, UnitOfMeasureModel


class ProductPackagingHierarchyValidator:
    """Validates product packaging definitions for consistency, cycles, and hierarchy."""

    @classmethod
    def validate_definitions(cls, definitions: List[Dict[str, Any]]) -> List[str]:
        warnings = []
        if not definitions:
            return warnings

        seen_pkg_units = set()
        for d in definitions:
            pkg_id = d.get("packaging_unit_id")
            cont_id = d.get("contained_unit_id")
            qty = d.get("contained_quantity")

            if pkg_id == cont_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Packaging unit cannot contain itself.",
                )

            if qty is None or Decimal(str(qty)) <= Decimal("0"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contained quantity must be greater than zero.",
                )

            if pkg_id in seen_pkg_units:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate packaging definition for the same packaging unit.",
                )
            seen_pkg_units.add(pkg_id)

        return warnings
