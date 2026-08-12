from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import INCIDENT_WRITE_ROLES, LOGISTICS_READ_ROLES
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.incident import (
    IncidentCreate,
    IncidentRead,
    IncidentResolve,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    IncidentUpdate,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidents"])
service = IncidentService()


@router.get("", response_model=PaginatedResponse[IncidentRead], summary="Listar incidencias")
def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    incident_status: IncidentStatus | None = Query(None, alias="status"),
    severity: IncidentSeverity | None = None,
    incident_type: IncidentType | None = None,
    shipment_id: UUID | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[IncidentRead]:
    return service.list(
        database,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        status=incident_status,
        severity=severity,
        incident_type=incident_type,
        shipment_id=shipment_id,
    )


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar incidencia",
    dependencies=[Depends(verify_csrf)],
)
def create_incident(
    data: IncidentCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*INCIDENT_WRITE_ROLES)),
) -> IncidentRead:
    return IncidentRead.model_validate(service.create(database, data, user))


@router.get("/{incident_id}", response_model=IncidentRead, summary="Consultar incidencia")
def get_incident(
    incident_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> IncidentRead:
    return IncidentRead.model_validate(service.get(database, incident_id))


@router.patch(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Actualizar incidencia",
    dependencies=[Depends(verify_csrf)],
)
def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*INCIDENT_WRITE_ROLES)),
) -> IncidentRead:
    return IncidentRead.model_validate(service.update(database, incident_id, data))


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentRead,
    summary="Resolver incidencia",
    dependencies=[Depends(verify_csrf)],
)
def resolve_incident(
    incident_id: UUID,
    data: IncidentResolve,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*INCIDENT_WRITE_ROLES)),
) -> IncidentRead:
    return IncidentRead.model_validate(service.resolve(database, incident_id, data, user))
