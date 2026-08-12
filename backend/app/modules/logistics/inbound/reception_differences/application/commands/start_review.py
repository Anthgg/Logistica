from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from ...application.services.case_service import ReceptionDifferenceCaseService
from ...application.services.review_service import ReceptionDifferenceReviewService
from app.modules.logistics.principal import LogisticsPrincipal


def start_review_command(db: Session, case_id: UUID, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    case = case_svc.transition_case(case_id, "UNDER_REVIEW", principal)
    review_svc = ReceptionDifferenceReviewService(db)
    review = review_svc.create_review(case_id, "OPERATIONAL", case.organization_id, principal)
    review = review_svc.start_review(review.id, case.organization_id, principal)
    return {"case_id": case_id, "status": case.status, "review_id": review.id}
