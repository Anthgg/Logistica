from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel


def now() -> datetime:
    return datetime.now(timezone.utc)


class ReceptionDifferenceNotificationService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, event_code: str, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_NOTIFICATION",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "case_code": case.case_code,
                "status": case.status,
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:notify:{case.id}:{event_code}:{event_id}",
            status="PENDING",
        ))

    def _get_case(self, case_id: UUID) -> ReceptionDifferenceCaseModel:
        case = self.db.get(ReceptionDifferenceCaseModel, case_id)
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)
        return case

    def notify_case_created(self, case_id: UUID, principal: LogisticsPrincipal) -> None:
        case = self._get_case(case_id)
        self._emit(case, "logistics.reception_difference.notification.case_created", {"created_by": str(principal.user_id)})

    def notify_submitted(self, case_id: UUID, principal: LogisticsPrincipal) -> None:
        case = self._get_case(case_id)
        self._emit(case, "logistics.reception_difference.notification.case_submitted", {"submitted_by": str(principal.user_id)})

    def notify_approved(self, case_id: UUID, principal: LogisticsPrincipal) -> None:
        case = self._get_case(case_id)
        self._emit(case, "logistics.reception_difference.notification.case_approved", {"approved_by": str(principal.user_id)})

    def notify_issued(self, case_id: UUID, principal: LogisticsPrincipal) -> None:
        case = self._get_case(case_id)
        self._emit(case, "logistics.reception_difference.notification.case_issued", {"issued_by": str(principal.user_id)})
