from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceMetricsProjectionModel,
    ReceptionDifferenceResponsiblePartyModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class ReceptionDifferenceMetricsProjectionService:
    def __init__(self, db: Session):
        self.db = db

    def recalculate(self, case_id: UUID, organization_id: UUID) -> ReceptionDifferenceMetricsProjectionModel:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ))

        total_items = len(items)
        critical_items = sum(1 for i in items if i.severity == "CRITICAL")
        quantity_items = sum(1 for i in items if i.category == "QUANTITY")
        product_items = sum(1 for i in items if i.category == "PRODUCT")
        condition_items = sum(1 for i in items if i.category == "CONDITION")
        identification_items = sum(1 for i in items if i.category == "IDENTIFICATION")
        documentation_items = sum(1 for i in items if i.category == "DOCUMENTATION")
        seal_items = sum(1 for i in items if i.category == "SEAL")

        evidence_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0

        photo_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
                ReceptionDifferenceEvidenceLinkModel.evidence_type.in_(["PRODUCT_PHOTO", "PACKAGING_PHOTO", "LABEL_PHOTO", "QUANTITY_COUNT_PHOTO", "DOCUMENT_PHOTO", "GUIDE_PHOTO", "SEAL_PHOTO"]),
            )
        ) or 0

        responsible_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceResponsiblePartyModel).where(
                ReceptionDifferenceResponsiblePartyModel.difference_case_id == case_id,
            )
        ) or 0

        projection = self.db.get(ReceptionDifferenceMetricsProjectionModel, case_id) or ReceptionDifferenceMetricsProjectionModel(case_id=case_id)
        projection.organization_id = case.organization_id
        projection.warehouse_id = case.warehouse_id
        projection.total_items = total_items
        projection.critical_items = critical_items
        projection.quantity_items = quantity_items
        projection.product_items = product_items
        projection.condition_items = condition_items
        projection.identification_items = identification_items
        projection.documentation_items = documentation_items
        projection.seal_items = seal_items
        projection.evidence_count = evidence_count
        projection.photo_count = photo_count
        projection.responsible_parties_count = responsible_count
        projection.calculated_at = now()

        self.db.add(projection)
        self.db.flush()

        case.item_count = total_items
        case.open_item_count = sum(1 for i in items if i.status not in ("SUPERSEDED", "CLOSED", "DISMISSED_WITH_REASON"))
        case.critical_item_count = critical_items
        case.evidence_count = evidence_count
        case.row_version += 1
        self.db.flush()

        return projection
