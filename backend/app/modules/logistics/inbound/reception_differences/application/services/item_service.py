from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.enums import (
    DIFFERENCE_TYPE_CATEGORY_MAP,
    CaseStatus,
    DifferenceType,
    ItemStatus,
    Severity,
)
from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff, require_item_transition
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def actor(principal: LogisticsPrincipal) -> dict[str, str]:
    return {"user_id": str(principal.user_id), "display_name": principal.full_name, "email": principal.email}


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


class ReceptionDifferenceItemService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, item_id: UUID | None = None, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        safe_metadata = metadata or {}
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_ITEM",
            aggregate_id=item_id or event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "item_id": str(item_id) if item_id else None,
                "occurred_at": timestamp.isoformat(),
                **safe_metadata,
            },
            deduplication_key=f"phase040:item:{item_id or event_id}:{event_code}:{event_id}",
            status="PENDING",
        ))
        AuditService().write_event(self.db, AuditEventCommand(
            event_code=event_code,
            actor_user_id=principal.user_id,
            actor_display_name=principal.full_name,
            actor_role_codes=principal.role_codes,
            session_id=principal.session_id,
            device_id=principal.device_id,
            authentication_level=principal.authentication_level,
            correlation_id=principal.correlation_id,
            ip_address=principal.ip_address,
            user_agent=principal.user_agent,
            organization_id=case.organization_id,
            branch_id=case.branch_id,
            warehouse_id=case.warehouse_id,
            resource_type="reception_difference_item",
            resource_id=str(item_id) if item_id else None,
            action=event_code.rsplit(".", 1)[-1],
            metadata=safe_metadata,
            source_module="logistics.inbound.reception_differences",
            source_service=self.__class__.__name__,
        ))

    def _get_case(self, case_id: UUID, organization_id: UUID) -> ReceptionDifferenceCaseModel:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)
        return case

    def _get_item(self, item_id: UUID, organization_id: UUID) -> ReceptionDifferenceItemModel:
        item = self.db.scalar(select(ReceptionDifferenceItemModel).join(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceItemModel.id == item_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not item:
            raise reception_difference_error("ReceptionDifferenceItemNotFound", "Ítem de diferencia no encontrado.", 404)
        return item

    def create_item(
        self,
        case_id: UUID,
        case_revision_id: UUID,
        organization_id: UUID,
        difference_type: str,
        title: str,
        description: str | None,
        product_id: UUID | None,
        severity: str | None,
        expected_quantity: Decimal | None,
        observed_quantity: Decimal | None,
        expected_unit_id: UUID | None,
        observed_unit_id: UUID | None,
        source_candidate_id: UUID | None,
        purchase_order_id: UUID | None,
        purchase_order_line_id: UUID | None,
        expected_line_id: UUID | None,
        received_line_id: UUID | None,
        detection_source: str,
        detected_by_user_id: UUID | None,
        detected_by_service: str | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceItemModel:
        case = self._get_case(case_id, organization_id)

        if case.status not in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION):
            raise reception_difference_error("ReceptionDifferenceCaseNotEditable", "El caso no admite nuevos ítems.", 409)

        max_item_number = self.db.scalar(
            select(func.max(ReceptionDifferenceItemModel.item_number))
            .where(ReceptionDifferenceItemModel.difference_case_id == case_id)
        ) or 0
        item_number = max_item_number + 1

        dt = DifferenceType(difference_type)
        category = DIFFERENCE_TYPE_CATEGORY_MAP.get(dt, "OTHER")

        resolved_severity = severity or SEVERITY_POLICY.get(category, Severity.LOW)

        expected_qty = Decimal(str(expected_quantity)) if expected_quantity is not None else Decimal("0")
        observed_qty = Decimal(str(observed_quantity)) if observed_quantity is not None else Decimal("0")
        diff_qty = expected_qty - observed_qty

        item = ReceptionDifferenceItemModel(
            id=uuid4(),
            difference_case_id=case_id,
            case_revision_id=case_revision_id,
            item_number=item_number,
            source_candidate_id=source_candidate_id,
            difference_type=difference_type,
            category=category,
            severity=resolved_severity,
            status=ItemStatus.OPEN,
            purchase_order_id=purchase_order_id,
            purchase_order_line_id=purchase_order_line_id,
            expected_line_id=expected_line_id,
            received_line_id=received_line_id,
            product_id=product_id,
            expected_quantity=expected_qty if expected_quantity is not None else None,
            expected_unit_id=expected_unit_id,
            observed_quantity=observed_qty if observed_quantity is not None else None,
            observed_unit_id=observed_unit_id,
            difference_quantity=diff_qty if expected_quantity is not None and observed_quantity is not None else None,
            difference_unit_id=observed_unit_id,
            title=title,
            description=description,
            detection_source=detection_source,
            detected_at=now(),
            detected_by_user_id=detected_by_user_id,
            detected_by_service=detected_by_service,
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

        self._emit(case, principal, "logistics.reception_difference.item_created", item_id=item.id, metadata={"difference_type": difference_type, "item_number": item_number})
        return item

    def list_items(self, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceItemModel]:
        self._get_case(case_id, organization_id)
        return list(self.db.scalars(
            select(ReceptionDifferenceItemModel)
            .where(ReceptionDifferenceItemModel.difference_case_id == case_id)
            .order_by(ReceptionDifferenceItemModel.item_number)
        ))

    def get_item(self, item_id: UUID, organization_id: UUID) -> ReceptionDifferenceItemModel:
        return self._get_item(item_id, organization_id)

    def update_item(self, item_id: UUID, organization_id: UUID, **fields) -> ReceptionDifferenceItemModel:
        item = self._get_item(item_id, organization_id)
        case = self._get_case(item.difference_case_id, organization_id)
        if case.status not in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION):
            raise reception_difference_error("ReceptionDifferenceCaseNotEditable", "El caso no admite ediciones.", 409)

        allowed_fields = {"title", "description", "severity", "difference_type"}
        for key, value in fields.items():
            if key in allowed_fields:
                setattr(item, key, value)
                if key == "difference_type":
                    dt = DifferenceType(value)
                    item.category = DIFFERENCE_TYPE_CATEGORY_MAP.get(dt, "OTHER")
        item.row_version += 1
        self.db.flush()
        return item

    def dismiss_item(self, item_id: UUID, organization_id: UUID, reason: str, principal: LogisticsPrincipal) -> ReceptionDifferenceItemModel:
        item = self._get_item(item_id, organization_id)
        require_item_transition(item.status, ItemStatus.DISMISSED_WITH_REASON)
        item.status = ItemStatus.DISMISSED_WITH_REASON
        item.row_version += 1

        case = self._get_case(item.difference_case_id, organization_id)
        case.open_item_count = max(case.open_item_count - 1, 0)
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.item_dismissed", item_id=item.id, metadata={"reason": reason})
        return item

    def supersede_item(self, item_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> ReceptionDifferenceItemModel:
        item = self._get_item(item_id, organization_id)
        require_item_transition(item.status, ItemStatus.SUPERSEDED)
        item.status = ItemStatus.SUPERSEDED
        item.row_version += 1

        case = self._get_case(item.difference_case_id, organization_id)
        case.open_item_count = max(case.open_item_count - 1, 0)
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.item_superseded", item_id=item.id)
        return item
