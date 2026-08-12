from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from app.modules.logistics.principal import LogisticsPrincipal


def request_changes_command(db: Session, case_id: UUID, reason: str, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    case = case_svc.transition_case(case_id, "CHANGES_REQUESTED", principal, reason=reason)
    return {"case_id": case_id, "status": case.status}
