from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...application.services.approval_service import ReceptionDifferenceApprovalService
from app.modules.logistics.principal import LogisticsPrincipal


def approve_case_command(db: Session, case_id: UUID, decision: str, reason: str | None, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    approval_svc = ReceptionDifferenceApprovalService(db)
    approval = approval_svc.create_approval_decision(case_id, decision, reason, case.organization_id, principal)
    if decision == "APPROVE_FOR_ISSUE":
        case = case_svc.transition_case(case_id, "APPROVED", principal)
    elif decision == "REQUEST_CHANGES":
        case = case_svc.transition_case(case_id, "CHANGES_REQUESTED", principal, reason=reason)
    return {"case_id": case_id, "status": case.status, "approval_id": approval.id}
