"""Service for generating and validating location full_codes (Phase 022)."""

from typing import Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.warehouses.models import WarehouseLocationModel
from app.modules.logistics.warehouses.validators import validate_location_segment


class WarehouseLocationCodeService:
    """Service to normalize segments, build hierarchical full_codes, and suggest next sequences."""

    @staticmethod
    def build_full_code(warehouse_code: str, parent_full_code: str | None, segment: str) -> str:
        clean_segment = segment.strip().upper()
        if parent_full_code:
            return f"{parent_full_code.strip().upper()}-{clean_segment}"
        return f"{warehouse_code.strip().upper()}-{clean_segment}"

    @staticmethod
    def recalculate_subtree_full_codes(
        db: Session, location: WarehouseLocationModel, new_parent_full_code: str | None, warehouse_code: str
    ) -> list[Tuple[UUID, str, str]]:
        """Recalculates full_code and hierarchy_path for a location and all its descendants.

        Returns a list of tuples: (location_id, old_full_code, new_full_code).
        """
        old_full_code = location.full_code
        new_full_code = WarehouseLocationCodeService.build_full_code(
            warehouse_code, new_parent_full_code, location.code
        )

        updates = [(location.id, old_full_code, new_full_code)]
        location.full_code = new_full_code
        location.hierarchy_path = f"{new_parent_full_code}/{location.id}" if new_parent_full_code else str(location.id)

        # Process children recursively
        children = db.scalars(
            select(WarehouseLocationModel).where(WarehouseLocationModel.parent_location_id == location.id)
        ).all()

        for child in children:
            child_updates = WarehouseLocationCodeService.recalculate_subtree_full_codes(
                db, child, new_full_code, warehouse_code
            )
            updates.extend(child_updates)

        return updates

    @staticmethod
    def suggest_next_code(
        db: Session, warehouse_id: UUID, parent_location_id: UUID | None, location_type: str
    ) -> str:
        """Suggests next sequential code prefix for a parent and type (e.g. Z01, A01, R01, N01, P01)."""
        prefix_map = {
            "ZONE": "Z",
            "AISLE": "A",
            "RACK": "R",
            "LEVEL": "N",
            "POSITION": "P",
            "DOCK": "DOCK",
            "STAGING": "STG",
            "RECEIVING": "REC",
            "DISPATCH": "DSP",
            "QUARANTINE": "QRN",
            "DAMAGED": "DMG",
        }
        prefix = prefix_map.get(location_type.upper(), location_type[:3].upper())

        siblings = db.scalars(
            select(WarehouseLocationModel).where(
                WarehouseLocationModel.warehouse_id == warehouse_id,
                WarehouseLocationModel.parent_location_id == parent_location_id,
                WarehouseLocationModel.location_type == location_type.upper(),
            )
        ).all()

        next_idx = len(siblings) + 1
        return f"{prefix}{str(next_idx).zfill(2)}"
