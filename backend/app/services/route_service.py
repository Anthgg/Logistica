from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.logistics_route import LogisticsRoute
from app.models.route_shipment import RouteShipment
from app.models.shipment import Shipment
from app.models.user import User
from app.repositories.route_repository import RouteRepository
from app.schemas.common import PaginatedResponse
from app.schemas.logistics_route import RouteCreate, RouteRead, RouteUpdate
from app.services.audit_service import AuditService


class RouteService:
    def __init__(self) -> None:
        self.repository = RouteRepository()
        self.audit = AuditService()

    def list(self, database: Session, **filters: object) -> PaginatedResponse[RouteRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[RouteRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get(self, database: Session, route_id: UUID, *, lock: bool = False) -> LogisticsRoute:
        route = self.repository.get(database, route_id, lock=lock)
        if not route:
            raise ApplicationError("ROUTE_NOT_FOUND", "La ruta no existe.", 404)
        return route

    def create(self, database: Session, data: RouteCreate, user: User) -> LogisticsRoute:
        if self.repository.get_by_code(database, data.route_code):
            raise ApplicationError("ROUTE_CODE_EXISTS", "El código de ruta ya existe.", 409)
        route = LogisticsRoute(**data.model_dump())
        database.add(route)
        database.flush()
        self.audit.record(
            database,
            "ROUTE_CREATED",
            user_id=user.id,
            resource_type="route",
            resource_id=str(route.id),
        )
        database.commit()
        database.refresh(route)
        return route

    def update(
        self, database: Session, route_id: UUID, data: RouteUpdate
    ) -> LogisticsRoute:
        route = self.get(database, route_id, lock=True)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(route, field, value)
        database.commit()
        database.refresh(route)
        return route

    def assign_shipments(
        self, database: Session, route_id: UUID, shipment_ids: list[UUID], user: User
    ) -> list[Shipment]:
        route = self.get(database, route_id, lock=True)
        if route.status == "cancelled":
            raise ApplicationError(
                "ROUTE_CANCELLED", "No se pueden asignar envíos a una ruta cancelada.", 409
            )
        if len(set(shipment_ids)) != len(shipment_ids):
            raise ApplicationError(
                "DUPLICATE_SHIPMENT_IN_REQUEST",
                "La solicitud contiene envíos duplicados.",
                422,
            )
        assigned: list[Shipment] = []
        for shipment_id in shipment_ids:
            shipment = database.scalar(
                select(Shipment).where(Shipment.id == shipment_id).with_for_update()
            )
            if not shipment:
                raise ApplicationError("SHIPMENT_NOT_FOUND", "El envío no existe.", 404)
            if shipment.status in {"delivered", "cancelled", "returned"}:
                raise ApplicationError(
                    "SHIPMENT_NOT_ASSIGNABLE",
                    f"El envío {shipment.tracking_code} no puede asignarse.",
                    409,
                )
            if self.repository.assignment(database, route.id, shipment.id):
                raise ApplicationError(
                    "SHIPMENT_ALREADY_ASSIGNED",
                    f"El envío {shipment.tracking_code} ya está en esta ruta.",
                    409,
                )
            if shipment.assigned_route_id and shipment.assigned_route_id != route.id:
                raise ApplicationError(
                    "SHIPMENT_ASSIGNED_TO_OTHER_ROUTE",
                    f"El envío {shipment.tracking_code} ya pertenece a otra ruta.",
                    409,
                )
            shipment.assigned_route_id = route.id
            database.add(
                RouteShipment(
                    route_id=route.id,
                    shipment_id=shipment.id,
                    assigned_by=user.id,
                )
            )
            assigned.append(shipment)
            self.audit.record(
                database,
                "SHIPMENT_ASSIGNED_TO_ROUTE",
                user_id=user.id,
                resource_type="shipment",
                resource_id=str(shipment.id),
                event_metadata={"route_id": str(route.id)},
            )
        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError(
                "SHIPMENT_ALREADY_ASSIGNED", "Uno de los envíos ya estaba asignado.", 409
            ) from exc
        return assigned

    def remove_shipment(
        self, database: Session, route_id: UUID, shipment_id: UUID
    ) -> None:
        self.get(database, route_id)
        assignment = self.repository.assignment(database, route_id, shipment_id)
        if not assignment:
            raise ApplicationError(
                "ROUTE_SHIPMENT_NOT_FOUND", "El envío no pertenece a esta ruta.", 404
            )
        shipment = database.get(Shipment, shipment_id)
        if shipment and shipment.assigned_route_id == route_id:
            shipment.assigned_route_id = None
        database.delete(assignment)
        database.commit()
