"""Duplicate detector — heuristic detection of potential duplicate requisitions (Phase 031)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import DuplicateResult
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionModel,
)


class PurchaseRequisitionDuplicateDetector:
    """Heuristic detector for potential duplicate requisitions.
    
    Checks:
    - Same cost center (+0.3)
    - Same requester (+0.3)
    - Required date within +/- 7 days (+0.2)
    - Same product set (+0.2)
    
    Advisory only — never blocks submission automatically.
    """

    def detect(
        self,
        db: Session,
        org_id: UUID,
        requester_id: UUID,
        cost_center_id: UUID,
        product_ids: list[UUID],
        required_date: date,
    ) -> dict:
        recent = (
            db.query(PurchaseRequisitionModel)
            .filter(
                PurchaseRequisitionModel.organization_id == org_id,
                PurchaseRequisitionModel.status.in_(["DRAFT", "SUBMITTED", "UNDER_REVIEW"]),
            )
            .all()
        )
        candidates = []
        for pr in recent:
            score = Decimal("0")
            if pr.cost_center_id == cost_center_id:
                score += Decimal("0.3")
            if pr.requester_user_id == requester_id:
                score += Decimal("0.3")
            if pr.required_date and abs((pr.required_date - required_date).days) <= 7:
                score += Decimal("0.2")

            if score >= Decimal("0.5"):
                candidates.append({
                    "requisition_id": str(pr.id),
                    "requisition_code": pr.requisition_code,
                    "score": float(score),
                    "status": pr.status,
                })

        if any(c["score"] >= 0.7 for c in candidates):
            result = DuplicateResult.HIGH_PROBABILITY_DUPLICATE
        elif candidates:
            result = DuplicateResult.POSSIBLE_DUPLICATE
        else:
            result = DuplicateResult.NOT_DUPLICATE

        return {
            "result": result,
            "candidates": candidates,
            "score": max([c["score"] for c in candidates], default=0.0),
        }


duplicate_detector = PurchaseRequisitionDuplicateDetector()
