from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import (
    LOGISTICS_READ_ROLES,
    SHIPMENT_STATUS_ROLES,
    SHIPMENT_WRITE_ROLES,
)
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentEventRead,
    ShipmentPriority,
    ShipmentRead,
    ShipmentStatus,
    ShipmentStatusUpdate,
    ShipmentUpdate,
)
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/shipments", tags=["Shipments"])
service = ShipmentService()


@router.get(
    "/",
    response_model=PaginatedResponse[ShipmentRead],
    include_in_schema=False,
)
@router.get("", response_model=PaginatedResponse[ShipmentRead], summary="Listar envíos")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    shipment_status: ShipmentStatus | None = Query(None, alias="status"),
    priority: ShipmentPriority | None = None,
    client_id: UUID | None = None,
    route_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[ShipmentRead]:
    return service.list(
        database,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        status=shipment_status,
        priority=priority,
        client_id=client_id,
        route_id=route_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post(
    "/",
    response_model=ShipmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)],
    include_in_schema=False,
)
@router.post(
    "",
    response_model=ShipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar envío",
    dependencies=[Depends(verify_csrf)],
)
def create_shipment(
    data: ShipmentCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*SHIPMENT_WRITE_ROLES)),
) -> ShipmentRead:
    return ShipmentRead.model_validate(service.create(database, data, user))


@router.get("/{shipment_id}", response_model=ShipmentRead, summary="Consultar envío")
def get_shipment(
    shipment_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> ShipmentRead:
    return ShipmentRead.model_validate(service.get(database, shipment_id))


@router.patch(
    "/{shipment_id}",
    response_model=ShipmentRead,
    summary="Actualizar datos permitidos del envío",
    dependencies=[Depends(verify_csrf)],
)
def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*SHIPMENT_WRITE_ROLES)),
) -> ShipmentRead:
    return ShipmentRead.model_validate(service.update(database, shipment_id, data))


@router.post(
    "/{shipment_id}/status",
    response_model=ShipmentRead,
    summary="Cambiar estado del envío",
    dependencies=[Depends(verify_csrf)],
)
def change_shipment_status(
    shipment_id: UUID,
    data: ShipmentStatusUpdate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*SHIPMENT_STATUS_ROLES)),
) -> ShipmentRead:
    return ShipmentRead.model_validate(
        service.change_status(database, shipment_id, data, user)
    )


@router.get(
    "/{shipment_id}/timeline",
    response_model=list[ShipmentEventRead],
    summary="Consultar historial inmutable del envío",
)
def shipment_timeline(
    shipment_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> list[ShipmentEventRead]:
    return service.timeline(database, shipment_id)
