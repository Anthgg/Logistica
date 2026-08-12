from __future__ import annotations
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from ...application.services.manual_creation_service import ManualReceptionDifferenceService
from ...application.services.case_service import ReceptionDifferenceCaseService
from app.modules.logistics.principal import LogisticsPrincipal


def create_manual_item_command(db: Session, case_id: UUID, difference_type: str, title: str, description: str | None, product_id: UUID | None, severity: str | None, observed_quantity: str | None, observed_unit_id: UUID | None, principal: LogisticsPrincipal) -> dict:
    case_svc = ReceptionDifferenceCaseService(db)
    case = case_svc.get_case(case_id, principal)
    svc = ManualReceptionDifferenceService(db)
    item = svc.create_manual_item(case_id, case.organization_id, difference_type, title, description, product_id, severity, Decimal(observed_quantity) if observed_quantity else None, observed_unit_id, principal)
    case_svc.recalculate_counts(case_id, case.organization_id)
    return {"item_id": item.id, "difference_type": item.difference_type, "severity": item.severity}
