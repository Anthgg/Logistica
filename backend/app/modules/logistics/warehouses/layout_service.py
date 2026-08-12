"""Service for 2D logical layout versions and logical map rendering (Phase 022)."""

import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.warehouses.models import (
    WarehouseLayoutNodeModel,
    WarehouseLayoutVersionModel,
    WarehouseLocationModel,
)
from app.modules.logistics.warehouses.schemas import (
    WarehouseLayoutNodeCreate,
    WarehouseLayoutVersionCreate,
)


class WarehouseLayoutService:
    """Service for 2D Warehouse Layout versions and React-consumable logical map payloads."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="warehouse_layout",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def create_layout_version(
        self, organization_id: UUID, warehouse_id: UUID, req: WarehouseLayoutVersionCreate, actor_id: UUID | None = None
    ) -> WarehouseLayoutVersionModel:
        wh = self.db.get(Warehouse, warehouse_id)
        if not wh or wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        # Find max version
        latest = self.db.scalars(
            select(WarehouseLayoutVersionModel)
            .where(WarehouseLayoutVersionModel.warehouse_id == warehouse_id)
            .order_by(WarehouseLayoutVersionModel.version.desc())
        ).first()

        new_version_num = (latest.version + 1) if latest else 1

        layout_ver = WarehouseLayoutVersionModel(
            warehouse_id=warehouse_id,
            version=new_version_num,
            name=req.name.strip(),
            status="DRAFT",
            canvas_width=req.canvas_width,
            canvas_height=req.canvas_height,
            floor_count=req.floor_count,
            created_by=actor_id,
        )
        self.db.add(layout_ver)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_layout.version_created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=layout_ver.id,
            details={"warehouse_id": str(warehouse_id), "version": layout_ver.version},
        )

        return layout_ver

    def add_node_to_layout(
        self, organization_id: UUID, layout_version_id: UUID, req: WarehouseLayoutNodeCreate, actor_id: UUID | None = None
    ) -> WarehouseLayoutNodeModel:
        ver = self.db.get(WarehouseLayoutVersionModel, layout_version_id)
        if not ver:
            raise HTTPException(status_code=404, detail="Versión de layout no encontrada.")

        wh = self.db.get(Warehouse, ver.warehouse_id)
        if wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no pertenece a la organización.")

        if ver.status == "ACTIVE":
            raise HTTPException(status_code=400, detail="No se pueden agregar nodos a un layout ACTIVO.")

        location = None
        if req.location_id:
            location = self.db.get(WarehouseLocationModel, req.location_id)
            if not location or location.warehouse_id != ver.warehouse_id:
                raise HTTPException(status_code=400, detail="La ubicación especificada no pertenece al almacén.")

        node = WarehouseLayoutNodeModel(
            warehouse_id=ver.warehouse_id,
            location_id=req.location_id,
            layout_version_id=layout_version_id,
            floor_index=req.floor_index,
            x=req.x,
            y=req.y,
            width=req.width,
            height=req.height,
            rotation_degrees=req.rotation_degrees,
            shape_type=req.shape_type.upper(),
            z_index=req.z_index,
            label_position=req.label_position.upper(),
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(node)
        self.db.flush()

        if location:
            location.layout_x = req.x
            location.layout_y = req.y
            location.layout_width = req.width
            location.layout_height = req.height
            location.layout_rotation = req.rotation_degrees
            location.floor_index = req.floor_index
            self.db.flush()

        return node

    def activate_layout_version(
        self, organization_id: UUID, layout_version_id: UUID, actor_id: UUID | None = None
    ) -> WarehouseLayoutVersionModel:
        ver = self.db.get(WarehouseLayoutVersionModel, layout_version_id)
        if not ver:
            raise HTTPException(status_code=404, detail="Versión de layout no encontrada.")

        wh = self.db.get(Warehouse, ver.warehouse_id)
        if wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no pertenece a la organización.")

        # Deprecate older active version
        active_versions = self.db.scalars(
            select(WarehouseLayoutVersionModel).where(
                and_(
                    WarehouseLayoutVersionModel.warehouse_id == ver.warehouse_id,
                    WarehouseLayoutVersionModel.status == "ACTIVE",
                )
            )
        ).all()
        for v in active_versions:
            v.status = "DEPRECATED"

        ver.status = "ACTIVE"
        ver.approved_by = actor_id
        ver.activated_at = utc_now()

        wh.layout_status = "ACTIVE"
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_layout.activated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=ver.id,
            details={"warehouse_id": str(ver.warehouse_id), "version": ver.version},
        )

        return ver

    def get_logical_map(
        self, organization_id: UUID, warehouse_id: UUID, floor_index: int = 1
    ) -> dict[str, Any]:
        """Returns JSON payload for React 2D map view."""
        wh = self.db.get(Warehouse, warehouse_id)
        if not wh or wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        # Get active or draft layout version
        ver = self.db.scalars(
            select(WarehouseLayoutVersionModel)
            .where(
                and_(
                    WarehouseLayoutVersionModel.warehouse_id == warehouse_id,
                    WarehouseLayoutVersionModel.status.in_(["ACTIVE", "DRAFT"]),
                )
            )
            .order_by(WarehouseLayoutVersionModel.status, WarehouseLayoutVersionModel.version.desc())
        ).first()

        if not ver:
            return {
                "warehouse_id": str(warehouse_id),
                "warehouse_code": wh.code,
                "layout_version": None,
                "canvas": {"width": 1000, "height": 1000, "floor_count": 1},
                "nodes": [],
            }

        nodes = self.db.scalars(
            select(WarehouseLayoutNodeModel).where(
                and_(
                    WarehouseLayoutNodeModel.layout_version_id == ver.id,
                    WarehouseLayoutNodeModel.floor_index == floor_index,
                )
            )
        ).all()

        formatted_nodes = []
        for n in nodes:
            loc = self.db.get(WarehouseLocationModel, n.location_id) if n.location_id else None
            formatted_nodes.append({
                "id": str(n.id),
                "location_id": str(n.location_id) if n.location_id else None,
                "location_code": loc.full_code if loc else None,
                "location_type": loc.location_type if loc else None,
                "x": float(n.x),
                "y": float(n.y),
                "width": float(n.width),
                "height": float(n.height),
                "rotation_degrees": float(n.rotation_degrees),
                "shape_type": n.shape_type,
                "z_index": n.z_index,
                "label_position": n.label_position,
            })

        return {
            "warehouse_id": str(warehouse_id),
            "warehouse_code": wh.code,
            "layout_version_id": str(ver.id),
            "version": ver.version,
            "status": ver.status,
            "canvas": {
                "width": float(ver.canvas_width),
                "height": float(ver.canvas_height),
                "floor_count": ver.floor_count,
                "current_floor": floor_index,
            },
            "nodes": formatted_nodes,
        }
