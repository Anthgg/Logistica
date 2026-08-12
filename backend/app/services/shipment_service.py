from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.models.client import Client
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.user import User
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.common import PaginatedResponse
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentEventRead,
    ShipmentRead,
    ShipmentStatusUpdate,
    ShipmentUpdate,
)
from app.services.audit_service import AuditService

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "registered": {"pending_pickup", "cancelled"},
    "pending_pickup": {"picked_up", "delayed", "cancelled"},
    "picked_up": {"warehouse_received", "in_transit", "delayed", "cancelled"},
    "warehouse_received": {"in_transit", "delayed", "returned", "cancelled"},
    "in_transit": {"out_for_delivery", "delayed", "returned"},
    "out_for_delivery": {"delivered", "delayed", "returned"},
    "delayed": {"pending_pickup", "picked_up", "warehouse_received", "in_transit", "out_for_delivery", "returned", "cancelled"},
    "delivered": {"returned"},
    "cancelled": set(),
    "returned": set(),
}


class ShipmentService:
    def __init__(self) -> None:
        self.repository = ShipmentRepository()
        self.audit = AuditService()

    def list(self, database: Session, **filters: object) -> PaginatedResponse[ShipmentRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[ShipmentRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get(self, database: Session, shipment_id: UUID, *, lock: bool = False) -> Shipment:
        shipment = self.repository.get(database, shipment_id, lock=lock)
        if not shipment:
            raise ApplicationError("SHIPMENT_NOT_FOUND", "El envío no existe.", 404)
        return shipment

    def create(self, database: Session, data: ShipmentCreate, user: User) -> Shipment:
        client = database.get(Client, data.client_id)
        if not client or not client.is_active:
            raise ApplicationError(
                "CLIENT_NOT_AVAILABLE", "El cliente no existe o está inactivo.", 422
            )
        sequence = database.execute(text("SELECT nextval('shipment_tracking_seq')")).scalar_one()
        tracking_code = f"ALG-{utc_now().year}-{int(sequence):06d}"
        shipment = Shipment(
            tracking_code=tracking_code,
            created_by=user.id,
            **data.model_dump(),
        )
        database.add(shipment)
        database.flush()
        event = ShipmentEvent(
            shipment_id=shipment.id,
            previous_status=None,
            new_status="registered",
            description="Envío registrado.",
            created_by=user.id,
        )
        database.add(event)
        self.audit.record(
            database,
            "SHIPMENT_CREATED",
            user_id=user.id,
            resource_type="shipment",
            resource_id=str(shipment.id),
            event_metadata={"tracking_code": tracking_code},
        )
        database.commit()
        database.refresh(shipment)
        return shipment

    def update(
        self, database: Session, shipment_id: UUID, data: ShipmentUpdate
    ) -> Shipment:
        shipment = self.get(database, shipment_id, lock=True)
        if shipment.status in {"delivered", "cancelled", "returned"}:
            raise ApplicationError(
                "SHIPMENT_NOT_EDITABLE",
                "El envío ya está en un estado terminal.",
                409,
            )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(shipment, field, value)
        database.commit()
        database.refresh(shipment)
        return shipment

    def change_status(
        self,
        database: Session,
        shipment_id: UUID,
        data: ShipmentStatusUpdate,
        user: User,
    ) -> Shipment:
        shipment = self.get(database, shipment_id, lock=True)
        new_status = data.status
        if new_status == shipment.status:
            raise ApplicationError(
                "SHIPMENT_STATUS_UNCHANGED", "El envío ya tiene ese estado.", 409
            )
        if new_status not in ALLOWED_TRANSITIONS[shipment.status]:
            raise ApplicationError(
                "INVALID_SHIPMENT_STATUS_TRANSITION",
                f"No se permite cambiar de {shipment.status} a {new_status}.",
                409,
            )
        previous = shipment.status
        shipment.status = new_status
        if new_status == "delivered":
            shipment.delivered_at = utc_now()
        database.add(
            ShipmentEvent(
                shipment_id=shipment.id,
                previous_status=previous,
                new_status=new_status,
                description=data.description,
                location=data.location,
                created_by=user.id,
            )
        )
        self.audit.record(
            database,
            "SHIPMENT_STATUS_CHANGED",
            user_id=user.id,
            resource_type="shipment",
            resource_id=str(shipment.id),
            event_metadata={"previous_status": previous, "new_status": new_status},
        )
        database.commit()
        database.refresh(shipment)
        return shipment

    def timeline(
        self, database: Session, shipment_id: UUID
    ) -> list[ShipmentEventRead]:
        self.get(database, shipment_id)
        return [
            ShipmentEventRead.model_validate(item)
            for item in self.repository.timeline(database, shipment_id)
        ]
