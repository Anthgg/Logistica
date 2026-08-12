from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from app.modules.logistics.principal import LogisticsPrincipal


def close_case_command(db: Session, case_id: UUID, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    case = case_svc.transition_case(case_id, "CLOSED", principal)
    return {"case_id": case_id, "status": case.status}
