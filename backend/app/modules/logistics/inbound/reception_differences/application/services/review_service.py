from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.enums import ReviewStatus, ReviewType
from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceReviewModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def actor(principal: LogisticsPrincipal) -> dict[str, str]:
    return {"user_id": str(principal.user_id), "display_name": principal.full_name, "email": principal.email}


class ReceptionDifferenceReviewService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_REVIEW",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:review:{case.id}:{event_code}:{event_id}",
            status="PENDING",
        ))
        AuditService().write_event(self.db, AuditEventCommand(
            event_code=event_code,
            actor_user_id=principal.user_id,
            actor_display_name=principal.full_name,
            actor_role_codes=principal.role_codes,
            session_id=principal.session_id,
            device_id=principal.device_id,
            authentication_level=principal.authentication_level,
            correlation_id=principal.correlation_id,
            ip_address=principal.ip_address,
            user_agent=principal.user_agent,
            organization_id=case.organization_id,
            branch_id=case.branch_id,
            warehouse_id=case.warehouse_id,
            resource_type="reception_difference_review",
            resource_id=str(event_id),
            action=event_code.rsplit(".", 1)[-1],
            metadata=metadata,
            source_module="logistics.inbound.reception_differences",
            source_service=self.__class__.__name__,
        ))

    def _get_case(self, case_id: UUID, organization_id: UUID) -> ReceptionDifferenceCaseModel:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)
        return case

    def _get_review(self, review_id: UUID, organization_id: UUID) -> ReceptionDifferenceReviewModel:
        review = self.db.scalar(select(ReceptionDifferenceReviewModel).join(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceReviewModel.id == review_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not review:
            raise reception_difference_error("ReceptionDifferenceReviewRequired", "Revisión no encontrada.", 404)
        return review

    def create_review(
        self,
        case_id: UUID,
        review_type: str,
        organization_id: UUID,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceReviewModel:
        case = self._get_case(case_id, organization_id)

        review = ReceptionDifferenceReviewModel(
            id=uuid4(),
            difference_case_id=case_id,
            review_type=review_type,
            status=ReviewStatus.PENDING,
            reviewer_user_id=principal.user_id,
            reviewer_snapshot=actor(principal),
        )
        self.db.add(review)
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.review_created", metadata={"review_id": str(review.id), "review_type": review_type})
        return review

    def start_review(self, review_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> ReceptionDifferenceReviewModel:
        review = self._get_review(review_id, organization_id)
        review.status = ReviewStatus.IN_PROGRESS
        self.db.flush()

        case = self._get_case(review.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.review_started", metadata={"review_id": str(review_id)})
        return review

    def request_changes(
        self,
        review_id: UUID,
        organization_id: UUID,
        changes: dict,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceReviewModel:
        review = self._get_review(review_id, organization_id)
        review.status = ReviewStatus.CHANGES_REQUESTED
        review.requested_changes = changes
        self.db.flush()

        case = self._get_case(review.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.review_changes_requested", metadata={"review_id": str(review_id)})
        return review

    def complete_review(
        self,
        review_id: UUID,
        organization_id: UUID,
        findings: str | None,
        blocking_issues: list | None,
        requested_changes: list | None,
        recommendation: str | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceReviewModel:
        review = self._get_review(review_id, organization_id)
        review.status = ReviewStatus.COMPLETED
        review.findings = findings
        review.blocking_issues = blocking_issues
        review.requested_changes = requested_changes
        review.recommendation = recommendation
        review.reviewed_at = now()
        self.db.flush()

        case = self._get_case(review.difference_case_id, organization_id)
        case.reviewed_at = now()
        case.reviewed_by = principal.user_id
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.review_completed", metadata={"review_id": str(review_id)})
        return review
