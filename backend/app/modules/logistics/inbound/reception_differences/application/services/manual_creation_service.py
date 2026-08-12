from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.enums import (
    DIFFERENCE_TYPE_CATEGORY_MAP,
    CaseStatus,
    DifferenceType,
    ItemStatus,
    Severity,
    SourceType,
)
from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


SEVERITY_POLICY: dict[str, str] = {
    "QUANTITY": Severity.MEDIUM,
    "PRODUCT": Severity.HIGH,
    "CONDITION": Severity.HIGH,
    "IDENTIFICATION": Severity.MEDIUM,
    "DOCUMENTATION": Severity.LOW,
    "SEAL": Severity.HIGH,
    "PROCESS": Severity.LOW,
    "SAFETY": Severity.CRITICAL,
    "OTHER": Severity.LOW,
}


class ManualReceptionDifferenceService:
    def __init__(self, db: Session):
        self.db = db

    def create_manual_item(
        self,
        case_id: UUID,
        organization_id: UUID,
        difference_type: str,
        title: str,
        description: str | None,
        product_id: UUID | None,
        severity: str | None,
        observed_quantity: Decimal,
        observed_unit_id: UUID | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceItemModel:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)
        if case.status not in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION):
            raise reception_difference_error("ReceptionDifferenceCaseNotEditable", "El caso no admite creación manual.", 409)

        dt = DifferenceType(difference_type)
        category = DIFFERENCE_TYPE_CATEGORY_MAP.get(dt, "OTHER")
        resolved_severity = severity or SEVERITY_POLICY.get(category, Severity.LOW)

        max_item_number = self.db.scalar(
            select(func.max(ReceptionDifferenceItemModel.item_number))
            .where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ) or 0
        item_number = max_item_number + 1

        observed_qty = Decimal(str(observed_quantity))

        item = ReceptionDifferenceItemModel(
            id=uuid4(),
            difference_case_id=case_id,
            case_revision_id=case.active_revision_id,
            item_number=item_number,
            difference_type=difference_type,
            category=category,
            severity=resolved_severity,
            status=ItemStatus.OPEN,
            product_id=product_id,
            observed_quantity=observed_qty,
            observed_unit_id=observed_unit_id,
            title=title,
            description=description,
            detection_source=SourceType.MANUAL_REVIEW,
            detected_at=now(),
            detected_by_user_id=principal.user_id,
            detected_by_service="ManualReceptionDifferenceService",
            requires_evidence=True,
            requires_responsibility=True,
        )
        self.db.add(item)
        self.db.flush()

        case.item_count += 1
        case.open_item_count += 1
        if resolved_severity == Severity.CRITICAL:
            case.critical_item_count += 1
        case.row_version += 1
        self.db.flush()
        return item
