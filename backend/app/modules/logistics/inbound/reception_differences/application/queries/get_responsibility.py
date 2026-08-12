from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...infrastructure.persistence.models import ReceptionDifferenceResponsiblePartyModel


def get_responsibility_query(db: Session, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceResponsiblePartyModel]:
    from .get_case import get_case_query
    get_case_query(db, case_id, organization_id)
    return list(db.scalars(select(ReceptionDifferenceResponsiblePartyModel).where(ReceptionDifferenceResponsiblePartyModel.difference_case_id == case_id).order_by(ReceptionDifferenceResponsiblePartyModel.created_at)))


def get_single_responsibility_query(db: Session, responsibility_id: UUID, organization_id: UUID) -> ReceptionDifferenceResponsiblePartyModel:
    from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel
    row = db.scalar(select(ReceptionDifferenceResponsiblePartyModel).join(ReceptionDifferenceCaseModel, ReceptionDifferenceCaseModel.id == ReceptionDifferenceResponsiblePartyModel.difference_case_id).where(ReceptionDifferenceResponsiblePartyModel.id == responsibility_id, ReceptionDifferenceCaseModel.organization_id == organization_id))
    if not row:
        from ...domain.errors import reception_difference_error
        raise reception_difference_error("RECEPTION_DIFFERENCE_RESPONSIBILITY_NOT_FOUND", "Responsable no encontrado.", 404)
    return row
