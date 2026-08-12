from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...infrastructure.persistence.models import ReceptionDifferenceItemModel


def get_items_query(db: Session, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceItemModel]:
    from .get_case import get_case_query
    get_case_query(db, case_id, organization_id)
    return list(db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case_id).order_by(ReceptionDifferenceItemModel.item_number)))


def get_item_query(db: Session, item_id: UUID, organization_id: UUID) -> ReceptionDifferenceItemModel:
    from sqlalchemy import select
    from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel
    item = db.scalar(select(ReceptionDifferenceItemModel).join(ReceptionDifferenceCaseModel, ReceptionDifferenceCaseModel.id == ReceptionDifferenceItemModel.difference_case_id).where(ReceptionDifferenceItemModel.id == item_id, ReceptionDifferenceCaseModel.organization_id == organization_id))
    if not item:
        from ...domain.errors import reception_difference_error
        raise reception_difference_error("RECEPTION_DIFFERENCE_ITEM_NOT_FOUND", "Ítem no encontrado.", 404)
    return item
