"""Revision service — lists and compares revisions (Phase 031)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionRevisionModel,
)


class PurchaseRequisitionRevisionService:
    """Manages revision querying and diff comparison."""

    def get_revision(
        self, db: Session, revision_id: UUID, org_id: UUID
    ) -> PurchaseRequisitionRevisionModel:
        rev = db.get(PurchaseRequisitionRevisionModel, revision_id)
        if rev is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REVISION_NOT_FOUND", "revision_id": str(revision_id)},
            )
        return rev

    def list_revisions(
        self, db: Session, requisition_id: UUID, org_id: UUID
    ) -> list[PurchaseRequisitionRevisionModel]:
        return (
            db.query(PurchaseRequisitionRevisionModel)
            .filter(PurchaseRequisitionRevisionModel.requisition_id == requisition_id)
            .order_by(PurchaseRequisitionRevisionModel.revision_number)
            .all()
        )

    def compare_revisions(
        self, db: Session, rev_id_a: UUID, rev_id_b: UUID, org_id: UUID
    ) -> dict:
        rev_a = self.get_revision(db, rev_id_a, org_id)
        rev_b = self.get_revision(db, rev_id_b, org_id)
        return {
            "revision_a": {
                "number": rev_a.revision_number,
                "status": rev_a.status,
                "justification": rev_a.justification,
                "line_count": rev_a.line_count,
            },
            "revision_b": {
                "number": rev_b.revision_number,
                "status": rev_b.status,
                "justification": rev_b.justification,
                "line_count": rev_b.line_count,
            },
            "changed_fields": [
                f for f in ["justification", "priority", "required_date"]
                if getattr(rev_a, f, None) != getattr(rev_b, f, None)
            ],
        }


revision_service = PurchaseRequisitionRevisionService()
