from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...application.services.document_service import ReceptionDifferenceDocumentService
from app.modules.logistics.principal import LogisticsPrincipal


def cancel_document_command(db: Session, case_id: UUID, reason: str, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    doc_svc = ReceptionDifferenceDocumentService(db)
    result = doc_svc.cancel_document(case_id, case.organization_id, reason, principal)
    return result
