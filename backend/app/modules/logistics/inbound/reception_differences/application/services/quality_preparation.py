from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


class QualityInspectionPreparationService:
    def __init__(self, db: Session):
        self.db = db

    def get_preparation(self, case_id: UUID, organization_id: UUID) -> dict:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ))

        quality_items = [i for i in items if i.requires_quality_review]
        condition_items = [i for i in items if i.category == "CONDITION"]
        safety_items = [i for i in items if i.category == "SAFETY"]

        return {
            "case_id": str(case_id),
            "case_code": case.case_code,
            "status": case.status,
            "quality_review_required": bool(quality_items),
            "quality_review_item_count": len(quality_items),
            "condition_item_count": len(condition_items),
            "safety_item_count": len(safety_items),
            "quarantine_recommended": any(i.future_quarantine_recommended for i in items),
            "items_needing_quality_review": [
                {"item_id": str(i.id), "item_number": i.item_number, "difference_type": i.difference_type, "severity": i.severity}
                for i in quality_items
            ],
            "future_capabilities": ["PHASE_041_QUALITY_INSPECTION"],
        }
