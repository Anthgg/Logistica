"""Hierarchy policy matrix for warehouse location parent-child compatibility (Phase 022)."""

from typing import Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.warehouses.models import WarehouseLocationModel

MAX_HIERARCHY_DEPTH = 10

ALLOWED_PARENTS: dict[str, set[str | None]] = {
    "ZONE": {None},
    "AISLE": {"ZONE"},
    "RACK": {"AISLE", "ZONE"},
    "LEVEL": {"RACK"},
    "POSITION": {"LEVEL", "RACK", "AISLE", "ZONE"},
    # Special types
    "DOCK": {None, "ZONE"},
    "STAGING": {None, "ZONE"},
    "RECEIVING": {None, "ZONE"},
    "DISPATCH": {None, "ZONE"},
    "CROSS_DOCK": {None, "ZONE"},
    "QUARANTINE": {None, "ZONE"},
    "RETURNS": {None, "ZONE"},
    "DAMAGED": {None, "ZONE"},
    "COLD_STORAGE": {None, "ZONE"},
    "BULK_STORAGE": {None, "ZONE"},
    "FLOOR_STORAGE": {None, "ZONE"},
    "VIRTUAL": {None},
    "OTHER": {None, "ZONE", "AISLE", "RACK"},
}


class WarehouseLocationHierarchyPolicy:
    """Enforces parent-child rules, max depth limits, and cycle detection."""

    @staticmethod
    def validate_parent_child(
        location_type: str, parent_type: str | None
    ) -> Tuple[bool, str]:
        location_type = location_type.upper()
        parent_type = parent_type.upper() if parent_type else None

        allowed = ALLOWED_PARENTS.get(location_type)
        if allowed is None:
            return False, f"Tipo de ubicación '{location_type}' no reconocido."

        if parent_type not in allowed:
            parent_desc = f"padre tipo '{parent_type}'" if parent_type else "sin padre (raíz)"
            return (
                False,
                f"Una ubicación tipo '{location_type}' no puede tener {parent_desc}. "
                f"Padres permitidos: {[p if p else 'RAÍZ' for p in allowed]}.",
            )

        return True, "OK"

    @staticmethod
    def check_cycles_and_depth(
        db: Session,
        target_location_id: UUID | None,
        new_parent_id: UUID | None,
        warehouse_id: UUID,
        organization_id: UUID,
    ) -> Tuple[int, str]:
        """Calculates new depth, verifies organization/warehouse boundary, and asserts no cycles."""
        if not new_parent_id:
            return 1, ""

        if target_location_id and target_location_id == new_parent_id:
            raise HTTPException(
                status_code=400, detail="Una ubicación no puede ser su propio padre."
            )

        visited = set()
        if target_location_id:
            visited.add(target_location_id)

        curr_id = new_parent_id
        depth_count = 1

        while curr_id:
            if curr_id in visited:
                raise HTTPException(
                    status_code=400,
                    detail="Ciclo detectado en la jerarquía de ubicaciones.",
                )
            visited.add(curr_id)

            parent = db.get(WarehouseLocationModel, curr_id)
            if not parent:
                raise HTTPException(
                    status_code=404, detail=f"Ubicación padre {curr_id} no encontrada."
                )

            if parent.organization_id != organization_id:
                raise HTTPException(
                    status_code=400,
                    detail="El padre pertenece a otra organización.",
                )

            if parent.warehouse_id != warehouse_id:
                raise HTTPException(
                    status_code=400,
                    detail="El padre pertenece a otro almacén.",
                )

            depth_count += 1
            if depth_count > MAX_HIERARCHY_DEPTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Profundidad máxima jerárquica ({MAX_HIERARCHY_DEPTH}) excedida.",
                )

            curr_id = parent.parent_location_id

        return depth_count, ""
