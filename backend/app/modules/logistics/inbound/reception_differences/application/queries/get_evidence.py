from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...infrastructure.persistence.models import ReceptionDifferenceEvidenceLinkModel


def get_evidence_query(db: Session, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceEvidenceLinkModel]:
    from .get_case import get_case_query
    get_case_query(db, case_id, organization_id)
    return list(db.scalars(select(ReceptionDifferenceEvidenceLinkModel).where(ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id, ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE").order_by(ReceptionDifferenceEvidenceLinkModel.created_at)))


def get_item_evidence_query(db: Session, item_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceEvidenceLinkModel]:
    from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel
    return list(db.scalars(select(ReceptionDifferenceEvidenceLinkModel).join(ReceptionDifferenceCaseModel, ReceptionDifferenceCaseModel.id == ReceptionDifferenceEvidenceLinkModel.difference_case_id).where(ReceptionDifferenceEvidenceLinkModel.difference_item_id == item_id, ReceptionDifferenceCaseModel.organization_id == organization_id, ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE")))
