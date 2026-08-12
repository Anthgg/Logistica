from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceAcknowledgementModel,
    ReceptionDifferenceApprovalModel,
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceCaseRevisionModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceResponsiblePartyModel,
    ReceptionDifferenceReviewModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def _row_dict(row: object) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class ReceptionDifferenceSnapshotProvider:
    def __init__(self, db: Session):
        self.db = db

    def capture(self, case_id: UUID, organization_id: UUID) -> dict:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        revisions = list(self.db.scalars(
            select(ReceptionDifferenceCaseRevisionModel)
            .where(ReceptionDifferenceCaseRevisionModel.difference_case_id == case_id)
            .order_by(ReceptionDifferenceCaseRevisionModel.revision_number)
        ))
        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ))
        evidence = list(self.db.scalars(
            select(ReceptionDifferenceEvidenceLinkModel).where(ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id)
        ))
        responsibilities = list(self.db.scalars(
            select(ReceptionDifferenceResponsiblePartyModel).where(ReceptionDifferenceResponsiblePartyModel.difference_case_id == case_id)
        ))
        reviews = list(self.db.scalars(
            select(ReceptionDifferenceReviewModel).where(ReceptionDifferenceReviewModel.difference_case_id == case_id)
        ))
        approvals = list(self.db.scalars(
            select(ReceptionDifferenceApprovalModel).where(ReceptionDifferenceApprovalModel.difference_case_id == case_id)
        ))
        acknowledgements = list(self.db.scalars(
            select(ReceptionDifferenceAcknowledgementModel).where(ReceptionDifferenceAcknowledgementModel.difference_case_id == case_id)
        ))

        revision_snapshots = []
        for rev in revisions:
            rev_items = [i for i in items if str(i.case_revision_id) == str(rev.id)]
            revision_snapshots.append({
                "revision_id": str(rev.id),
                "revision_number": rev.revision_number,
                "status": rev.status,
                "source_snapshot": rev.source_snapshot,
                "items_snapshot": jsonable_encoder([_row_dict(i) for i in rev_items]),
                "content_hash": rev.content_hash,
                "created_at": rev.created_at.isoformat() if rev.created_at else None,
                "frozen_at": rev.frozen_at.isoformat() if rev.frozen_at else None,
            })

        return {
            "canonicalization_version": "1",
            "case": jsonable_encoder(_row_dict(case)),
            "revisions": revision_snapshots,
            "items": jsonable_encoder([_row_dict(i) for i in items]),
            "evidence": jsonable_encoder([_row_dict(e) for e in evidence]),
            "responsibility": jsonable_encoder([_row_dict(r) for r in responsibilities]),
            "review": jsonable_encoder([_row_dict(r) for r in reviews]),
            "approval": jsonable_encoder([_row_dict(a) for a in approvals]),
            "acknowledgement": jsonable_encoder([_row_dict(a) for a in acknowledgements]),
            "captured_at": now().isoformat(),
        }
