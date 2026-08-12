"""Service for managing location capacities and restrictions (Phase 022)."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.warehouses.models import (
    WarehouseLocationCapacityModel,
    WarehouseLocationModel,
    WarehouseLocationRestrictionModel,
)
from app.modules.logistics.warehouses.schemas import (
    WarehouseLocationCapacityCreate,
    WarehouseLocationRestrictionCreate,
)
from app.modules.logistics.warehouses.validators import (
    VALID_CAPACITY_TYPES,
    VALID_RESTRICTION_TYPES,
)


class WarehouseCapacityRestrictionService:
    """Service for managing location capacity limits and physical/environmental restrictions."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="location_capacity_restriction",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def add_capacity(
        self, organization_id: UUID, location_id: UUID, req: WarehouseLocationCapacityCreate, actor_id: UUID | None = None
    ) -> WarehouseLocationCapacityModel:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        cap_type = req.capacity_type.upper()
        if cap_type not in VALID_CAPACITY_TYPES:
            raise HTTPException(status_code=400, detail=f"Tipo de capacidad '{cap_type}' no soportado.")

        if req.maximum_value <= 0:
            raise HTTPException(status_code=400, detail="El valor máximo de capacidad debe ser mayor a 0.")

        cap = WarehouseLocationCapacityModel(
            location_id=location_id,
            capacity_type=cap_type,
            maximum_value=req.maximum_value,
            unit_code=req.unit_code.strip().upper(),
            warning_threshold=req.warning_threshold,
            critical_threshold=req.critical_threshold,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(cap)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.capacity_added",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=cap.id,
            details={"location_id": str(location_id), "capacity_type": cap.capacity_type, "max_value": str(cap.maximum_value)},
        )

        return cap

    def list_capacities(self, organization_id: UUID, location_id: UUID) -> list[WarehouseLocationCapacityModel]:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        return list(
            self.db.scalars(
                select(WarehouseLocationCapacityModel).where(
                    WarehouseLocationCapacityModel.location_id == location_id
                )
            ).all()
        )

    def add_restriction(
        self, organization_id: UUID, location_id: UUID, req: WarehouseLocationRestrictionCreate, actor_id: UUID | None = None
    ) -> WarehouseLocationRestrictionModel:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        res_type = req.restriction_type.upper()
        if res_type not in VALID_RESTRICTION_TYPES:
            raise HTTPException(status_code=400, detail=f"Tipo de restricción '{res_type}' no soportado.")

        res = WarehouseLocationRestrictionModel(
            location_id=location_id,
            restriction_type=res_type,
            operator=req.operator.upper(),
            value_payload=req.value_payload,
            severity=req.severity.upper(),
            is_blocking=req.is_blocking,
            reason=req.reason,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(res)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.restriction_added",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=res.id,
            details={"location_id": str(location_id), "restriction_type": res.restriction_type, "severity": res.severity},
        )

        return res

    def list_restrictions(self, organization_id: UUID, location_id: UUID) -> list[WarehouseLocationRestrictionModel]:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        return list(
            self.db.scalars(
                select(WarehouseLocationRestrictionModel).where(
                    WarehouseLocationRestrictionModel.location_id == location_id
                )
            ).all()
        )
