from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


class FutureQuarantineRecommendationService:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self, case_id: UUID, organization_id: UUID) -> list[dict]:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(
                ReceptionDifferenceItemModel.difference_case_id == case_id,
                ReceptionDifferenceItemModel.future_quarantine_recommended == True,
            )
        ))

        return [
            {
                "item_id": str(i.id),
                "item_number": i.item_number,
                "difference_type": i.difference_type,
                "category": i.category,
                "severity": i.severity,
                "product_id": str(i.product_id) if i.product_id else None,
                "title": i.title,
                "future_capabilities": ["PHASE_042_QUARANTINE"],
            }
            for i in items
        ]
