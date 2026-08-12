from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.formalization_service import ReceptionDifferenceCandidateFormalizationService
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...domain.errors import reception_difference_error
from app.modules.logistics.principal import LogisticsPrincipal


def formalize_candidates_command(db: Session, case_id: UUID, candidate_ids: list[UUID], principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    formalization_svc = ReceptionDifferenceCandidateFormalizationService(db)
    items = formalization_svc.formalize_candidates(case_id, candidate_ids, case.organization_id, principal)
    case_svc.recalculate_counts(case_id, case.organization_id)
    return {"case_id": case_id, "items_created": len(items), "item_ids": [str(i.id) for i in items]}
