from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...application.services.document_service import ReceptionDifferenceDocumentService
from ...application.services.notification_service import ReceptionDifferenceNotificationService
from app.modules.logistics.principal import LogisticsPrincipal


def issue_document_command(db: Session, case_id: UUID, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    doc_svc = ReceptionDifferenceDocumentService(db)
    result = doc_svc.issue_document(case_id, case.organization_id, principal)
    case = case_svc.transition_case(case_id, "ISSUED", principal)
    ReceptionDifferenceNotificationService(db).notify_issued(case_id, principal)
    return result
