"""Service for managing Warehouse entities (Phase 022)."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.branch import Branch
from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.warehouses.schemas import WarehouseCreate, WarehouseUpdate
from app.modules.logistics.warehouses.validators import (
    VALID_WAREHOUSE_TYPES,
    validate_warehouse_code,
)


class WarehouseService:
    """Service for Warehouse management using existing Warehouse entity."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="warehouses",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def list_warehouses(
        self,
        organization_id: UUID,
        branch_id: UUID | None = None,
        warehouse_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Warehouse]:
        query = select(Warehouse).where(
            Warehouse.organization_id == organization_id
        )

        if branch_id:
            query = query.where(Warehouse.branch_id == branch_id)
        if warehouse_type:
            query = query.where(Warehouse.warehouse_type == warehouse_type.upper())
        if status:
            query = query.where(Warehouse.status == status.upper())
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(Warehouse.name.ilike(pattern) | Warehouse.code.ilike(pattern))

        return list(self.db.scalars(query.order_by(Warehouse.code)).all())

    def get_warehouse(self, organization_id: UUID, warehouse_id: UUID) -> Warehouse | None:
        wh = self.db.get(Warehouse, warehouse_id)
        if wh and wh.organization_id == organization_id:
            return wh
        return None

    def create_warehouse(
        self, organization_id: UUID, req: WarehouseCreate, actor_id: UUID | None = None
    ) -> Warehouse:
        is_valid, clean_code = validate_warehouse_code(req.code)
        if not is_valid:
            raise HTTPException(status_code=400, detail=clean_code)

        # Validate Branch belongs to Organization
        branch = self.db.get(Branch, req.branch_id)
        if not branch or branch.organization_id != organization_id:
            raise HTTPException(status_code=400, detail="La sede especificada no pertenece a la organización.")

        # Check unique code in organization
        existing = self.db.scalars(
            select(Warehouse).where(
                and_(Warehouse.organization_id == organization_id, Warehouse.code == clean_code)
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código de almacén '{clean_code}' ya existe en la organización.")

        wh_type = req.warehouse_type.upper()
        if wh_type not in VALID_WAREHOUSE_TYPES:
            raise HTTPException(status_code=400, detail=f"Tipo de almacén '{wh_type}' inválido.")

        wh = Warehouse(
            organization_id=organization_id,
            branch_id=req.branch_id,
            code=clean_code,
            name=req.name.strip(),
            description=req.description,
            warehouse_type=wh_type,
            address=req.address,
            uses_branch_location=req.uses_branch_location,
            latitude=None if req.uses_branch_location else req.latitude,
            longitude=None if req.uses_branch_location else req.longitude,
            address_id=req.address_id,
            district=req.district,
            province=req.province,
            department=req.department,
            capacity=req.capacity,
            status="ACTIVE",
            layout_status="DRAFT",
            manager_user_id=req.manager_user_id,
            operating_hours=req.operating_hours,
            temperature_controlled=req.temperature_controlled,
            hazardous_materials_allowed=req.hazardous_materials_allowed,
            cross_dock_enabled=req.cross_dock_enabled,
            receiving_enabled=req.receiving_enabled,
            dispatch_enabled=req.dispatch_enabled,
            inventory_enabled=req.inventory_enabled,
            is_default=req.is_default,
            created_by=actor_id,
        )
        self.db.add(wh)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=wh.id,
            details={"code": wh.code, "name": wh.name, "branch_id": str(wh.branch_id)},
        )

        return wh

    def update_warehouse(
        self, organization_id: UUID, warehouse_id: UUID, req: WarehouseUpdate, actor_id: UUID | None = None
    ) -> Warehouse:
        wh = self.get_warehouse(organization_id, warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        # Code inmutability for active warehouses
        if req.code is not None and req.code.strip().upper() != wh.code:
            if wh.status == "ACTIVE":
                raise HTTPException(status_code=400, detail="No se puede modificar el código de un almacén ACTIVO.")
            is_valid, clean_code = validate_warehouse_code(req.code)
            if not is_valid:
                raise HTTPException(status_code=400, detail=clean_code)
            wh.code = clean_code

        for field in [
            "name", "description", "address", "address_id", "district", "province",
            "department", "capacity", "manager_user_id", "operating_hours",
            "temperature_controlled", "hazardous_materials_allowed",
            "cross_dock_enabled", "receiving_enabled", "dispatch_enabled",
            "inventory_enabled", "is_default"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                setattr(wh, field, val)

        if req.warehouse_type is not None:
            wh.warehouse_type = req.warehouse_type.upper()

        if "uses_branch_location" in req.model_fields_set:
            wh.uses_branch_location = bool(req.uses_branch_location)
            if wh.uses_branch_location:
                wh.latitude = None
                wh.longitude = None
            else:
                wh.latitude = req.latitude
                wh.longitude = req.longitude
        elif "latitude" in req.model_fields_set or "longitude" in req.model_fields_set:
            if wh.uses_branch_location:
                raise HTTPException(
                    status_code=422,
                    detail="Desactiva la ubicación heredada antes de guardar coordenadas propias.",
                )
            wh.latitude = req.latitude
            wh.longitude = req.longitude

        wh.updated_by = actor_id
        wh.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=wh.id,
            details={"name": wh.name, "status": wh.status},
        )

        return wh

    def set_warehouse_status(
        self, organization_id: UUID, warehouse_id: UUID, status: str, actor_id: UUID | None = None
    ) -> Warehouse:
        wh = self.get_warehouse(organization_id, warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        status = status.upper()
        wh.status = status
        wh.updated_by = actor_id
        wh.updated_at = utc_now()
        self.db.flush()

        event_code = f"logistics.warehouse.{status.lower()}" if status in ("ACTIVATED", "DEACTIVATED", "ARCHIVED") else "logistics.warehouse.updated"
        self._write_audit(
            event_code=event_code,
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=wh.id,
            details={"status": status},
        )

        return wh
