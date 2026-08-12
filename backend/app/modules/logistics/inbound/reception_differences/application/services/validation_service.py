from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff
from ...infrastructure.persistence.models import (
    ReceptionDifferenceApprovalModel,
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceResponsiblePartyModel,
    ReceptionDifferenceReviewModel,
)


class ReceptionDifferenceValidationService:
    def __init__(self, db: Session):
        self.db = db

    def validate(self, case_id: UUID, organization_id: UUID) -> dict:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        errors: list[str] = []
        warnings: list[str] = []

        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ))
        if not items:
            errors.append("NO_ITEMS")

        open_items = [i for i in items if i.status in ("OPEN", "EVIDENCE_PENDING", "RESPONSIBILITY_PENDING", "READY_FOR_REVIEW")]
        if open_items:
            errors.append("OPEN_ITEMS_REMAINING")

        critical_items = [i for i in items if i.severity == "CRITICAL"]

        evidence_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0
        if evidence_count == 0 and items:
            warnings.append("NO_EVIDENCE")

        resp_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceResponsiblePartyModel).where(
                ReceptionDifferenceResponsiblePartyModel.difference_case_id == case_id,
            )
        ) or 0
        if resp_count == 0 and items:
            warnings.append("NO_RESPONSIBILITY")

        review_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceReviewModel).where(
                ReceptionDifferenceReviewModel.difference_case_id == case_id,
            )
        ) or 0

        approval_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceApprovalModel).where(
                ReceptionDifferenceApprovalModel.difference_case_id == case_id,
            )
        ) or 0

        is_ready_for_issue = not errors and case.status in ("APPROVED", "ISSUED")
        result = {
            "case_id": str(case_id),
            "is_valid": not errors,
            "blocking_errors": errors,
            "warnings": warnings,
            "item_count": len(items),
            "open_item_count": len(open_items),
            "critical_item_count": len(critical_items),
            "evidence_count": evidence_count,
            "responsible_party_count": resp_count,
            "review_count": review_count,
            "approval_count": approval_count,
            "is_ready_for_issue": is_ready_for_issue,
            "validation_hash": canonical_hash_diff({"case_id": str(case_id), "errors": errors, "warnings": warnings}),
        }
        return result
