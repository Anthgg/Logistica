from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.incident import Incident


class IncidentRepository:
    def get(self, database: Session, incident_id: UUID, *, lock: bool = False) -> Incident | None:
        stmt = select(Incident).where(Incident.id == incident_id)
        if lock:
            stmt = stmt.with_for_update()
        return database.scalar(stmt)

    def list(
        self,
        database: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status: str | None = None,
        severity: str | None = None,
        incident_type: str | None = None,
        shipment_id: UUID | None = None,
    ) -> Tuple[List[Incident], int]:
        filters = []
        if status:
            filters.append(Incident.status == status)
        if severity:
            filters.append(Incident.severity == severity)
        if incident_type:
            filters.append(Incident.incident_type == incident_type)
        if shipment_id:
            filters.append(Incident.shipment_id == shipment_id)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Incident.title.ilike(pattern),
                    Incident.description.ilike(pattern),
                )
            )

        total = database.scalar(select(func.count()).select_from(Incident).where(*filters)) or 0

        sort_col = getattr(Incident, sort_by, Incident.created_at)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()

        items = list(
            database.scalars(
                select(Incident)
                .where(*filters)
                .order_by(sort_col)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total
