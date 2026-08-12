"""Service for managing WarehouseLocation hierarchy, subtrees and moves (Phase 022)."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.warehouses.code_service import WarehouseLocationCodeService
from app.modules.logistics.warehouses.hierarchy_policy import WarehouseLocationHierarchyPolicy
from app.modules.logistics.warehouses.models import (
    WarehouseLocationCodeAliasModel,
    WarehouseLocationModel,
)
from app.modules.logistics.warehouses.schemas import (
    WarehouseLocationCreate,
    WarehouseLocationMovePreviewResponse,
    WarehouseLocationUpdate,
)
from app.modules.logistics.warehouses.validators import (
    validate_location_segment,
    VALID_LOCATION_TYPES,
    VALID_USAGE_TYPES,
)


class WarehouseLocationService:
    """Service for Location hierarchy, full_code stability, subtree operations, and moves."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="warehouse_locations",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def get_location(self, organization_id: UUID, location_id: UUID) -> WarehouseLocationModel | None:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if loc and loc.organization_id == organization_id:
            return loc
        return None

    def list_locations(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        parent_location_id: UUID | None = None,
        location_type: str | None = None,
        status: str | None = None,
    ) -> list[WarehouseLocationModel]:
        query = select(WarehouseLocationModel).where(
            and_(
                WarehouseLocationModel.organization_id == organization_id,
                WarehouseLocationModel.warehouse_id == warehouse_id,
            )
        )
        if parent_location_id is not None:
            query = query.where(WarehouseLocationModel.parent_location_id == parent_location_id)
        if location_type:
            query = query.where(WarehouseLocationModel.location_type == location_type.upper())
        if status:
            query = query.where(WarehouseLocationModel.status == status.upper())

        return list(self.db.scalars(query.order_by(WarehouseLocationModel.sequence_order, WarehouseLocationModel.code)).all())

    def create_location(
        self, organization_id: UUID, req: WarehouseLocationCreate, actor_id: UUID | None = None
    ) -> WarehouseLocationModel:
        # Validate Warehouse
        wh = self.db.get(Warehouse, req.warehouse_id)
        if not wh or wh.organization_id != organization_id:
            raise HTTPException(status_code=400, detail="El almacén especificado no pertenece a la organización.")

        loc_type = req.location_type.upper()
        if loc_type not in VALID_LOCATION_TYPES:
            raise HTTPException(status_code=400, detail=f"Tipo de ubicación '{loc_type}' no soportado.")

        # Validate segment syntax
        is_valid_seg, clean_code = validate_location_segment(req.code)
        if not is_valid_seg:
            raise HTTPException(status_code=400, detail=clean_code)

        # Validate parent
        parent = None
        parent_type = None
        parent_full_code = None

        if req.parent_location_id:
            parent = self.get_location(organization_id, req.parent_location_id)
            if not parent or parent.warehouse_id != req.warehouse_id:
                raise HTTPException(status_code=400, detail="Ubicación padre no válida o pertenece a otro almacén.")
            parent_type = parent.location_type
            parent_full_code = parent.full_code

        # Validate hierarchy matrix
        ok_matrix, msg_matrix = WarehouseLocationHierarchyPolicy.validate_parent_child(loc_type, parent_type)
        if not ok_matrix:
            raise HTTPException(status_code=400, detail=msg_matrix)

        # Check depth and cycles
        depth, _ = WarehouseLocationHierarchyPolicy.check_cycles_and_depth(
            self.db, None, req.parent_location_id, req.warehouse_id, organization_id
        )

        full_code = WarehouseLocationCodeService.build_full_code(wh.code, parent_full_code, clean_code)

        # Check unique full_code in organization
        existing = self.db.scalars(
            select(WarehouseLocationModel).where(
                and_(
                    WarehouseLocationModel.organization_id == organization_id,
                    WarehouseLocationModel.full_code == full_code,
                )
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"La ubicación con código completo '{full_code}' ya existe.")

        hierarchy_path = f"{parent.hierarchy_path}/{req.parent_location_id}" if parent else str(wh.id)

        loc = WarehouseLocationModel(
            organization_id=organization_id,
            branch_id=wh.branch_id,
            warehouse_id=req.warehouse_id,
            parent_location_id=req.parent_location_id,
            location_type=loc_type,
            code=clean_code,
            full_code=full_code,
            name=req.name.strip(),
            description=req.description,
            hierarchy_path=hierarchy_path,
            depth=depth,
            sequence_order=req.sequence_order,
            status=req.status.upper(),
            usage_type=req.usage_type.upper(),
            picking_priority=req.picking_priority,
            putaway_priority=req.putaway_priority,
            is_pickable=req.is_pickable,
            is_receivable=req.is_receivable,
            is_dispatchable=req.is_dispatchable,
            is_countable=req.is_countable,
            is_locked=req.is_locked,
            lock_reason=req.lock_reason,
            layout_x=req.layout_x,
            layout_y=req.layout_y,
            layout_width=req.layout_width,
            layout_height=req.layout_height,
            layout_rotation=req.layout_rotation,
            floor_index=req.floor_index,
            created_by=actor_id,
        )
        self.db.add(loc)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=loc.id,
            details={"full_code": loc.full_code, "location_type": loc.location_type, "warehouse_id": str(loc.warehouse_id)},
        )

        return loc

    def update_location(
        self, organization_id: UUID, location_id: UUID, req: WarehouseLocationUpdate, actor_id: UUID | None = None
    ) -> WarehouseLocationModel:
        loc = self.get_location(organization_id, location_id)
        if not loc:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        for field in [
            "name", "description", "sequence_order", "picking_priority",
            "putaway_priority", "is_pickable", "is_receivable", "is_dispatchable",
            "is_countable", "is_locked", "lock_reason", "layout_x", "layout_y",
            "layout_width", "layout_height", "layout_rotation", "floor_index"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                setattr(loc, field, val)

        if req.status is not None:
            loc.status = req.status.upper()
        if req.usage_type is not None:
            loc.usage_type = req.usage_type.upper()

        loc.updated_by = actor_id
        loc.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=loc.id,
            details={"full_code": loc.full_code, "status": loc.status},
        )

        return loc

    def move_preview(
        self, organization_id: UUID, location_id: UUID, new_parent_location_id: UUID | None
    ) -> WarehouseLocationMovePreviewResponse:
        loc = self.get_location(organization_id, location_id)
        if not loc:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        wh = self.db.get(Warehouse, loc.warehouse_id)
        new_parent = None
        new_parent_type = None
        new_parent_full_code = None

        if new_parent_location_id:
            new_parent = self.get_location(organization_id, new_parent_location_id)
            if not new_parent or new_parent.warehouse_id != loc.warehouse_id:
                raise HTTPException(status_code=400, detail="Nuevo padre no pertenece al mismo almacén.")
            new_parent_type = new_parent.location_type
            new_parent_full_code = new_parent.full_code

        ok_matrix, msg_matrix = WarehouseLocationHierarchyPolicy.validate_parent_child(loc.location_type, new_parent_type)
        if not ok_matrix:
            raise HTTPException(status_code=400, detail=msg_matrix)

        WarehouseLocationHierarchyPolicy.check_cycles_and_depth(
            self.db, location_id, new_parent_location_id, loc.warehouse_id, organization_id
        )

        # Count descendants
        descendants = self.get_descendants(organization_id, location_id)
        new_full_code = WarehouseLocationCodeService.build_full_code(wh.code, new_parent_full_code, loc.code)

        warnings = []
        if loc.status == "ACTIVE":
            warnings.append("Mover una ubicación ACTIVA afectará los códigos de todos los nodos descendientes.")

        return WarehouseLocationMovePreviewResponse(
            location_id=loc.id,
            current_parent_id=loc.parent_location_id,
            new_parent_id=new_parent_location_id,
            current_full_code=loc.full_code,
            proposed_full_code=new_full_code,
            descendants_affected_count=len(descendants),
            warnings=warnings,
            is_move_allowed=True,
        )

    def move_location(
        self,
        organization_id: UUID,
        location_id: UUID,
        new_parent_location_id: UUID | None,
        reason: str,
        actor_id: UUID | None = None,
    ) -> WarehouseLocationModel:
        preview = self.move_preview(organization_id, location_id, new_parent_location_id)
        loc = self.get_location(organization_id, location_id)
        wh = self.db.get(Warehouse, loc.warehouse_id)

        new_parent_full_code = None
        if new_parent_location_id:
            parent = self.get_location(organization_id, new_parent_location_id)
            new_parent_full_code = parent.full_code

        old_full_code = loc.full_code
        loc.parent_location_id = new_parent_location_id

        # Recalculate subtree full_codes and record aliases
        updates = WarehouseLocationCodeService.recalculate_subtree_full_codes(
            self.db, loc, new_parent_full_code, wh.code
        )

        for l_id, prev_code, new_code in updates:
            if prev_code != new_code:
                alias = WarehouseLocationCodeAliasModel(
                    location_id=l_id,
                    previous_full_code=prev_code,
                    new_full_code=new_code,
                    reason=reason,
                    created_by=actor_id,
                )
                self.db.add(alias)

        loc.updated_by = actor_id
        loc.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.moved",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=loc.id,
            details={
                "previous_full_code": old_full_code,
                "new_full_code": loc.full_code,
                "descendants_affected": len(updates),
                "reason": reason,
            },
        )

        return loc

    def get_descendants(self, organization_id: UUID, location_id: UUID) -> list[WarehouseLocationModel]:
        loc = self.get_location(organization_id, location_id)
        if not loc:
            return []

        # Recursive list using hierarchy_path search
        pattern = f"%{location_id}%"
        return list(
            self.db.scalars(
                select(WarehouseLocationModel).where(
                    and_(
                        WarehouseLocationModel.organization_id == organization_id,
                        WarehouseLocationModel.warehouse_id == loc.warehouse_id,
                        WarehouseLocationModel.id != location_id,
                        WarehouseLocationModel.hierarchy_path.like(pattern),
                    )
                )
            ).all()
        )

    def get_tree(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        root_location_id: UUID | None = None,
        max_depth: int = 10,
    ) -> dict[str, Any]:
        """Builds a nested tree structure of locations for frontend consumption."""
        wh = self.db.get(Warehouse, warehouse_id)
        if not wh or wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        locations = self.list_locations(organization_id, warehouse_id)
        nodes_by_id = {str(l.id): l for l in locations}

        tree_nodes = []
        children_map = {}
        for l in locations:
            p_id = str(l.parent_location_id) if l.parent_location_id else None
            children_map.setdefault(p_id, []).append(l)

        def build_node(l: WarehouseLocationModel) -> dict[str, Any]:
            children_locs = children_map.get(str(l.id), [])
            return {
                "id": str(l.id),
                "code": l.code,
                "full_code": l.full_code,
                "name": l.name,
                "location_type": l.location_type,
                "status": l.status,
                "usage_type": l.usage_type,
                "depth": l.depth,
                "sequence_order": l.sequence_order,
                "mapped": bool(l.layout_x is not None and l.layout_y is not None),
                "is_pickable": l.is_pickable,
                "is_receivable": l.is_receivable,
                "is_dispatchable": l.is_dispatchable,
                "children": [build_node(c) for c in children_locs],
            }

        root_parents = children_map.get(str(root_location_id) if root_location_id else None, [])
        return {
            "warehouse_id": str(warehouse_id),
            "warehouse_code": wh.code,
            "total_nodes": len(locations),
            "tree": [build_node(r) for r in root_parents],
        }
