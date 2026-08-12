from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
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
    SourceType,
)
from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)
from app.modules.logistics.inbound.receiving.infrastructure.persistence.models import (
    ReceptionDifferenceCandidateModel,
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


class ReceptionDifferenceCandidateFormalizationService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, item_id: UUID | None = None, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        safe_metadata = metadata or {}
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_FORMALIZATION",
            aggregate_id=item_id or event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "item_id": str(item_id) if item_id else None,
                "occurred_at": timestamp.isoformat(),
                **safe_metadata,
            },
            deduplication_key=f"phase040:formalize:{item_id or event_id}:{event_code}:{event_id}",
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

    def _get_candidate(self, candidate_id: UUID) -> ReceptionDifferenceCandidateModel:
        candidate = self.db.get(ReceptionDifferenceCandidateModel, candidate_id)
        if not candidate:
            raise reception_difference_error("ReceptionDifferenceCandidateNotFound", "Candidato no encontrado.", 404)
        return candidate

    def _create_item_from_candidate(
        self,
        candidate: ReceptionDifferenceCandidateModel,
        case: ReceptionDifferenceCaseModel,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceItemModel:
        from .item_service import ReceptionDifferenceItemService
        item_svc = ReceptionDifferenceItemService(self.db)

        candidate_type = candidate.candidate_type
        diff_type = DifferenceType.SHORTAGE if "SHORTAGE" in candidate_type else DifferenceType.OVERAGE
        category = DIFFERENCE_TYPE_CATEGORY_MAP.get(diff_type, "OTHER")
        severity = SEVERITY_POLICY.get(category, Severity.LOW)

        expected_base = Decimal(str(candidate.expected_value.get("base_quantity", "0"))) if candidate.expected_value else Decimal("0")
        observed_base = Decimal(str(candidate.observed_value.get("base_quantity", "0"))) if candidate.observed_value else Decimal("0")
        diff_qty = expected_base - observed_base

        item = item_svc.create_item(
            case_id=case.id,
            case_revision_id=case.active_revision_id,
            organization_id=case.organization_id,
            difference_type=diff_type,
            title=f"{candidate_type} - {candidate.expected_line_id}",
            description=None,
            product_id=None,
            severity=severity,
            expected_quantity=expected_base,
            observed_quantity=observed_base,
            expected_unit_id=candidate.unit_id,
            observed_unit_id=candidate.unit_id,
            source_candidate_id=candidate.id,
            purchase_order_id=None,
            purchase_order_line_id=None,
            expected_line_id=candidate.expected_line_id,
            received_line_id=candidate.received_line_id,
            detection_source=SourceType.RECEIPT_CANDIDATES,
            detected_by_user_id=None,
            detected_by_service="ReceptionDifferenceCandidateFormalizationService",
            principal=principal,
        )
        return item

    def formalize_candidates(
        self,
        case_id: UUID,
        candidate_ids: list[UUID],
        organization_id: UUID,
        principal: LogisticsPrincipal,
    ) -> list[ReceptionDifferenceItemModel]:
        case = self._get_case(case_id, organization_id)
        if case.status not in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION):
            raise reception_difference_error("ReceptionDifferenceCaseNotEditable", "El caso no admite formalizaciones.", 409)

        items: list[ReceptionDifferenceItemModel] = []
        for candidate_id in candidate_ids:
            candidate = self._get_candidate(candidate_id)
            if candidate.inbound_receipt_id != case.inbound_receipt_id:
                raise reception_difference_error("ReceptionDifferenceCandidateInvalid", "El candidato no pertenece a la recepción del caso.", 409)
            if candidate.status == "PREPARED_FOR_PHASE_040":
                raise reception_difference_error("ReceptionDifferenceCandidateAlreadyFormalized", "El candidato ya fue formalizado.", 409)

            item = self._create_item_from_candidate(candidate, case, principal)
            candidate.status = "PREPARED_FOR_PHASE_040"
            items.append(item)
            self._emit(case, principal, "logistics.reception_difference.candidate_formalized", item_id=item.id, metadata={"candidate_id": str(candidate.id)})

        self.db.flush()
        return items

    def formalize_single_candidate(
        self,
        candidate_id: UUID,
        case_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceItemModel:
        items = self.formalize_candidates(case_id, [candidate_id], organization_id, principal)
        return items[0]
