from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import LOGISTICS_READ_ROLES, ROUTE_WRITE_ROLES
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.i18n import translate
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.logistics_route import (
    RouteCreate,
    RouteRead,
    RouteShipmentAssignment,
    RouteStatus,
    RouteUpdate,
)
from app.schemas.shipment import ShipmentRead
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])
service = RouteService()


@router.get("", response_model=PaginatedResponse[RouteRead], summary="Listar rutas")
def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("scheduled_date"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    route_status: RouteStatus | None = Query(None, alias="status"),
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[RouteRead]:
    return service.list(
        database,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        status=route_status,
    )


@router.post(
    "",
    response_model=RouteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ruta",
    dependencies=[Depends(verify_csrf)],
)
def create_route(
    data: RouteCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*ROUTE_WRITE_ROLES)),
) -> RouteRead:
    return RouteRead.model_validate(service.create(database, data, user))


@router.get("/{route_id}", response_model=RouteRead, summary="Consultar ruta")
def get_route(
    route_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> RouteRead:
    return RouteRead.model_validate(service.get(database, route_id))


@router.patch(
    "/{route_id}",
    response_model=RouteRead,
    summary="Actualizar ruta",
    dependencies=[Depends(verify_csrf)],
)
def update_route(
    route_id: UUID,
    data: RouteUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*ROUTE_WRITE_ROLES)),
) -> RouteRead:
    return RouteRead.model_validate(service.update(database, route_id, data))


@router.post(
    "/{route_id}/assign-shipments",
    response_model=list[ShipmentRead],
    summary="Asignar envíos a una ruta",
    dependencies=[Depends(verify_csrf)],
)
def assign_shipments(
    route_id: UUID,
    data: RouteShipmentAssignment,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*ROUTE_WRITE_ROLES)),
) -> list[ShipmentRead]:
    return [
        ShipmentRead.model_validate(item)
        for item in service.assign_shipments(database, route_id, data.shipment_ids, user)
    ]


@router.delete(
    "/{route_id}/shipments/{shipment_id}",
    summary="Retirar envío de una ruta",
    dependencies=[Depends(verify_csrf)],
)
def remove_shipment(
    route_id: UUID,
    shipment_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*ROUTE_WRITE_ROLES)),
) -> dict[str, object]:
    service.remove_shipment(database, route_id, shipment_id)
    return {
        "success": True,
        "message": translate("message.route.shipment_removed"),
    }
