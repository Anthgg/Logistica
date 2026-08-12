from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.models.incident import Incident
from app.models.shipment import Shipment
from app.models.user import User
from app.repositories.incident_repository import IncidentRepository
from app.schemas.common import PaginatedResponse
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentResolve, IncidentUpdate
from app.services.audit_service import AuditService


class IncidentService:
    def __init__(self) -> None:
        self.repository = IncidentRepository()
        self.audit = AuditService()

    def list(self, database: Session, **filters: object) -> PaginatedResponse[IncidentRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[IncidentRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get(self, database: Session, incident_id: UUID, *, lock: bool = False) -> Incident:
        incident = self.repository.get(database, incident_id, lock=lock)
        if not incident:
            raise ApplicationError("INCIDENT_NOT_FOUND", "La incidencia no existe.", 404)
        return incident

    def create(self, database: Session, data: IncidentCreate, user: User) -> Incident:
        if data.shipment_id and not database.get(Shipment, data.shipment_id):
            raise ApplicationError("SHIPMENT_NOT_FOUND", "El envío no existe.", 422)
        incident = Incident(
            **data.model_dump(),
            reported_by=user.id,
        )
        database.add(incident)
        database.flush()
        self.audit.record(
            database,
            "INCIDENT_CREATED",
            user_id=user.id,
            resource_type="incident",
            resource_id=str(incident.id),
        )
        database.commit()
        database.refresh(incident)
        return incident

    def update(
        self, database: Session, incident_id: UUID, data: IncidentUpdate
    ) -> Incident:
        incident = self.get(database, incident_id, lock=True)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("status") == "resolved":
            raise ApplicationError(
                "USE_RESOLVE_ENDPOINT",
                "Use el endpoint de resolución para cerrar la incidencia.",
                422,
            )
        for field, value in changes.items():
            setattr(incident, field, value)
        database.commit()
        database.refresh(incident)
        return incident

    def resolve(
        self,
        database: Session,
        incident_id: UUID,
        data: IncidentResolve,
        user: User,
    ) -> Incident:
        incident = self.get(database, incident_id, lock=True)
        if incident.status in {"resolved", "closed"}:
            raise ApplicationError(
                "INCIDENT_ALREADY_RESOLVED", "La incidencia ya fue resuelta.", 409
            )
        incident.status = "resolved"
        incident.resolution = data.resolution
        incident.resolved_at = utc_now()
        incident.assigned_to = user.id
        self.audit.record(
            database,
            "INCIDENT_RESOLVED",
            user_id=user.id,
            resource_type="incident",
            resource_id=str(incident.id),
        )
        database.commit()
        database.refresh(incident)
        return incident
