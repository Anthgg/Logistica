from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent


class ShipmentRepository:
    SORT_FIELDS = {
        "created_at": Shipment.created_at,
        "updated_at": Shipment.updated_at,
        "tracking_code": Shipment.tracking_code,
        "status": Shipment.status,
        "priority": Shipment.priority,
        "expected_delivery_at": Shipment.expected_delivery_at,
    }

    def get(self, database: Session, shipment_id: UUID, *, lock: bool = False) -> Shipment | None:
        statement = select(Shipment).where(Shipment.id == shipment_id)
        if lock:
            statement = statement.with_for_update()
        return database.scalar(statement)

    def list(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: str,
        status: str | None,
        priority: str | None,
        client_id: UUID | None,
        route_id: UUID | None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[Shipment], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Shipment.tracking_code.ilike(term),
                    Shipment.package_description.ilike(term),
                    Shipment.destination_address.ilike(term),
                )
            )
        if status:
            filters.append(Shipment.status == status)
        if priority:
            filters.append(Shipment.priority == priority)
        if client_id:
            filters.append(Shipment.client_id == client_id)
        if route_id:
            filters.append(Shipment.assigned_route_id == route_id)
        if date_from:
            filters.append(Shipment.created_at >= date_from)
        if date_to:
            filters.append(Shipment.created_at <= date_to)
        total = database.scalar(
            select(func.count()).select_from(Shipment).where(*filters)
        ) or 0
        column = self.SORT_FIELDS[sort_by]
        ordering = column.desc() if sort_order == "desc" else column.asc()
        return (
            list(
                database.scalars(
                    select(Shipment)
                    .where(*filters)
                    .order_by(ordering)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ),
            total,
        )

    def timeline(self, database: Session, shipment_id: UUID) -> list[ShipmentEvent]:
        return list(
            database.scalars(
                select(ShipmentEvent)
                .where(ShipmentEvent.shipment_id == shipment_id)
                .order_by(ShipmentEvent.created_at.asc())
            )
        )
