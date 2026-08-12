from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


class FutureClaimPreparationService:
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
            select(ReceptionDifferenceItemModel).where(
                ReceptionDifferenceItemModel.difference_case_id == case_id,
                ReceptionDifferenceItemModel.future_claim_recommended == True,
            )
        ))

        return {
            "case_id": str(case_id),
            "case_code": case.case_code,
            "status": case.status,
            "claim_recommended": bool(items),
            "claim_item_count": len(items),
            "supplier_id": str(case.supplier_business_partner_id) if case.supplier_business_partner_id else None,
            "supplier_snapshot": case.supplier_snapshot,
            "carrier_id": str(case.carrier_business_partner_id) if case.carrier_business_partner_id else None,
            "carrier_snapshot": case.carrier_snapshot,
            "items_for_claim": [
                {
                    "item_id": str(i.id),
                    "item_number": i.item_number,
                    "difference_type": i.difference_type,
                    "category": i.category,
                    "severity": i.severity,
                    "title": i.title,
                }
                for i in items
            ],
            "future_capabilities": ["PHASE_043_CLAIM"],
        }
