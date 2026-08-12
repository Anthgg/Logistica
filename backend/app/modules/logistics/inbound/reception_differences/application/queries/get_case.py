from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel, ReceptionDifferenceCaseRevisionModel


def get_case_query(db: Session, case_id: UUID, organization_id: UUID) -> ReceptionDifferenceCaseModel:
    case = db.scalar(select(ReceptionDifferenceCaseModel).where(ReceptionDifferenceCaseModel.id == case_id, ReceptionDifferenceCaseModel.organization_id == organization_id))
    if not case:
        from ...domain.errors import reception_difference_error
        raise reception_difference_error("RECEPTION_DIFFERENCE_CASE_NOT_FOUND", "Caso no encontrado.", 404)
    return case


def get_case_summary(db: Session, case_id: UUID, organization_id: UUID) -> dict:
    case = get_case_query(db, case_id, organization_id)
    from ..services.case_service import ReceptionDifferenceCaseService
    svc = ReceptionDifferenceCaseService(db)
    capabilities = svc.get_capabilities(case_id, organization_id)
    return {
        "id": case.id, "case_code": case.case_code, "status": case.status, "severity": case.severity,
        "item_count": case.item_count, "open_item_count": case.open_item_count,
        "critical_item_count": case.critical_item_count, "evidence_count": case.evidence_count,
        "responsibility_status": case.responsibility_status, "source_type": case.source_type,
        "created_at": case.created_at, "updated_at": case.updated_at,
        "capabilities": capabilities.get("actions", []),
    }
