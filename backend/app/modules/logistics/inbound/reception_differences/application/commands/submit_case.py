from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...application.services.notification_service import ReceptionDifferenceNotificationService
from app.modules.logistics.principal import LogisticsPrincipal


def submit_case_command(db: Session, case_id: UUID, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    case = case_svc.transition_case(case_id, "SUBMITTED_FOR_REVIEW", principal)
    ReceptionDifferenceNotificationService(db).notify_submitted(case_id, principal)
    return {"case_id": case_id, "status": case.status}
