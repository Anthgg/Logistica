"""Background jobs for Phase 040 reception differences."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceMetricsProjectionModel,
)

logger = logging.getLogger(__name__)


def detect_incomplete_cases(db: Session) -> list[dict]:
    cases = list(db.scalars(
        select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.status.in_(["DRAFT", "UNDER_PREPARATION", "PENDING_EVIDENCE", "PENDING_RESPONSIBILITY"]),
        )
    ))
    results = []
    for case in cases:
        items = list(db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id)))
        open_items = [i for i in items if i.status in ("OPEN", "EVIDENCE_PENDING", "RESPONSIBILITY_PENDING")]
        if open_items:
            results.append({"case_id": str(case.id), "case_code": case.case_code, "open_items": len(open_items), "status": case.status})
    return results


def detect_pending_evidence(db: Session) -> list[dict]:
    items = list(db.scalars(
        select(ReceptionDifferenceItemModel).where(
            ReceptionDifferenceItemModel.requires_evidence == True,
            ReceptionDifferenceItemModel.status.in_(["OPEN", "EVIDENCE_PENDING"]),
        )
    ))
    results = []
    for item in items:
        evidence_count = db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_item_id == item.id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0
        if evidence_count == 0:
            results.append({"item_id": str(item.id), "case_id": str(item.difference_case_id), "difference_type": item.difference_type})
    return results


def detect_pending_responsibility(db: Session) -> list[dict]:
    from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.models import ReceptionDifferenceResponsiblePartyModel
    cases = list(db.scalars(
        select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.status.in_(["UNDER_PREPARATION", "PENDING_RESPONSIBILITY", "SUBMITTED_FOR_REVIEW"]),
            ReceptionDifferenceCaseModel.responsibility_status == "UNDETERMINED",
        )
    ))
    return [{"case_id": str(c.id), "case_code": c.case_code} for c in cases]


def detect_critical_without_approval(db: Session) -> list[dict]:
    cases = list(db.scalars(
        select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.severity == "CRITICAL",
            ReceptionDifferenceCaseModel.status.in_(["READY_FOR_APPROVAL", "APPROVED"]),
        )
    ))
    return [{"case_id": str(c.id), "case_code": c.case_code, "status": c.status} for c in cases]


def update_metrics_projection(db: Session, case_id=None) -> int:
    query = select(ReceptionDifferenceCaseModel)
    if case_id:
        query = query.where(ReceptionDifferenceCaseModel.id == case_id)
    cases = list(db.scalars(query))
    updated = 0
    for case in cases:
        items = list(db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id)))
        evidence_count = db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0
        projection = db.get(ReceptionDifferenceMetricsProjectionModel, case.id)
        if not projection:
            projection = ReceptionDifferenceMetricsProjectionModel(case_id=case.id, organization_id=case.organization_id, warehouse_id=case.warehouse_id)
            db.add(projection)
        projection.total_items = len(items)
        projection.critical_items = sum(1 for i in items if i.severity == "CRITICAL")
        projection.quantity_items = sum(1 for i in items if i.category == "QUANTITY")
        projection.product_items = sum(1 for i in items if i.category == "PRODUCT")
        projection.condition_items = sum(1 for i in items if i.category == "CONDITION")
        projection.identification_items = sum(1 for i in items if i.category == "IDENTIFICATION")
        projection.documentation_items = sum(1 for i in items if i.category == "DOCUMENTATION")
        projection.seal_items = sum(1 for i in items if i.category == "SEAL")
        projection.evidence_count = evidence_count
        projection.calculated_at = datetime.now(timezone.utc)
        updated += 1
    db.flush()
    return updated


def detect_candidates_not_formalized(db: Session) -> list[dict]:
    from app.modules.logistics.inbound.receiving.infrastructure.persistence.models import ReceptionDifferenceCandidateModel
    candidates = list(db.scalars(
        select(ReceptionDifferenceCandidateModel).where(
            ReceptionDifferenceCandidateModel.status.in_(["OPEN", "ACKNOWLEDGED"]),
        )
    ))
    return [{"candidate_id": str(c.id), "receipt_id": str(c.inbound_receipt_id), "type": c.candidate_type} for c in candidates]
