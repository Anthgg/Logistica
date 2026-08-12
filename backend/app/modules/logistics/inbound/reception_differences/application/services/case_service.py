from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.enums import CaseStatus, CaseRevisionStatus, DIFFERENCE_TYPE_CATEGORY_MAP, Severity
from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff, require_case_transition, strict_decimal_diff
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceCaseRevisionModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceMetricsProjectionModel,
    ReceptionDifferenceResponsiblePartyModel,
    ReceptionDifferenceReviewModel,
    ReceptionDifferenceApprovalModel,
    ReceptionDifferenceAcknowledgementModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def actor(principal: LogisticsPrincipal) -> dict[str, str]:
    return {"user_id": str(principal.user_id), "display_name": principal.full_name, "email": principal.email}


class ReceptionDifferenceCaseService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, reason: str | None = None, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        safe_metadata = metadata or {}
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_CASE",
            aggregate_id=case.id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "warehouse_id": str(case.warehouse_id),
                "case_code": case.case_code,
                "status": case.status,
                "occurred_at": timestamp.isoformat(),
                **safe_metadata,
            },
            deduplication_key=f"phase040:{case.id}:{event_code}:{event_id}",
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
            resource_type="reception_difference_case",
            resource_id=str(case.id),
            action=event_code.rsplit(".", 1)[-1],
            reason_text=reason,
            metadata=safe_metadata,
            source_module="logistics.inbound.reception_differences",
            source_service=self.__class__.__name__,
        ))

    def _get_case(self, case_id: UUID, organization_id: UUID, *, lock: bool = False) -> ReceptionDifferenceCaseModel:
        query = select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        case = self.db.scalar(query)
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)
        return case

    def create_case(
        self,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        inbound_receipt_id: UUID,
        receipt_revision_id: UUID,
        source_type: str,
        supplier_snapshot: dict,
        carrier_snapshot: dict | None,
        unloading_operation_id: UUID | None,
        gate_check_in_id: UUID | None,
        appointment_id: UUID | None,
        arrival_notice_id: UUID | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceCaseModel:
        timestamp = now()
        case_code = f"DIF-{timestamp.year}-{uuid4().hex[:12].upper()}"
        normalized_code = case_code.upper()

        case = ReceptionDifferenceCaseModel(
            id=uuid4(),
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            case_code=case_code,
            normalized_case_code=normalized_code,
            inbound_receipt_id=inbound_receipt_id,
            inbound_receipt_revision_id=receipt_revision_id,
            unloading_operation_id=unloading_operation_id,
            gate_check_in_id=gate_check_in_id,
            appointment_id=appointment_id,
            arrival_notice_id=arrival_notice_id,
            supplier_business_partner_id=None,
            supplier_snapshot=supplier_snapshot or {},
            carrier_snapshot=carrier_snapshot,
            status=CaseStatus.DRAFT,
            source_type=source_type,
            severity=Severity.LOW,
            item_count=0,
            open_item_count=0,
            critical_item_count=0,
            evidence_count=0,
            responsibility_status="UNDETERMINED",
            created_by=principal.user_id,
        )
        self.db.add(case)
        self.db.flush()

        revision = ReceptionDifferenceCaseRevisionModel(
            id=uuid4(),
            difference_case_id=case.id,
            revision_number=1,
            status=CaseRevisionStatus.EDITABLE,
            source_snapshot=jsonable_encoder({
                "inbound_receipt_id": str(inbound_receipt_id),
                "receipt_revision_id": str(receipt_revision_id),
                "source_type": source_type,
                "supplier_snapshot": supplier_snapshot,
                "carrier_snapshot": carrier_snapshot,
            }),
            created_by=principal.user_id,
        )
        self.db.add(revision)
        self.db.flush()

        case.active_revision_id = revision.id
        case.current_revision_number = 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.case_created")
        return case

    def get_case(self, case_id: UUID, organization_id_or_principal) -> ReceptionDifferenceCaseModel:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        return self._get_case(case_id, organization_id)

    def recalculate_counts(self, case_id: UUID, organization_id: UUID) -> None:
        case = self._get_case(case_id, organization_id, lock=True)
        items = list(self.db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id)))
        case.item_count = len(items)
        case.open_item_count = sum(1 for i in items if i.status in ("OPEN", "EVIDENCE_PENDING", "RESPONSIBILITY_PENDING", "READY_FOR_REVIEW"))
        case.critical_item_count = sum(1 for i in items if i.severity == Severity.CRITICAL)
        case.evidence_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0
        max_severity = Severity.LOW
        severity_order = [Severity.INFORMATIONAL, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        for item in items:
            idx = severity_order.index(Severity(item.severity)) if item.severity in [s.value for s in severity_order] else 0
            max_idx = severity_order.index(max_severity)
            if idx > max_idx:
                max_severity = Severity(item.severity)
        case.severity = max_severity
        case.row_version += 1
        self.db.flush()

    def list_cases(self, organization_id_or_principal, filters: dict | None = None, page: int = 1, page_size: int = 20) -> tuple[list[ReceptionDifferenceCaseModel], int]:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        query = select(ReceptionDifferenceCaseModel).where(ReceptionDifferenceCaseModel.organization_id == organization_id)
        count_query = select(func.count()).select_from(ReceptionDifferenceCaseModel).where(ReceptionDifferenceCaseModel.organization_id == organization_id)

        filters = filters or {}
        if "status" in filters:
            query = query.where(ReceptionDifferenceCaseModel.status == filters["status"])
            count_query = count_query.where(ReceptionDifferenceCaseModel.status == filters["status"])
        if "warehouse_id" in filters:
            query = query.where(ReceptionDifferenceCaseModel.warehouse_id == filters["warehouse_id"])
            count_query = count_query.where(ReceptionDifferenceCaseModel.warehouse_id == filters["warehouse_id"])
        if "severity" in filters:
            query = query.where(ReceptionDifferenceCaseModel.severity == filters["severity"])
            count_query = count_query.where(ReceptionDifferenceCaseModel.severity == filters["severity"])

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        items = list(self.db.scalars(query.order_by(ReceptionDifferenceCaseModel.created_at.desc()).offset(offset).limit(page_size)))
        return items, total

    def update_case(self, case_id: UUID, organization_id: UUID, principal: LogisticsPrincipal, **fields) -> ReceptionDifferenceCaseModel:
        from app.modules.logistics.auth_dependencies import resolve_organization_id
        if isinstance(organization_id, LogisticsPrincipal):
            organization_id = resolve_organization_id(organization_id)
        case = self._get_case(case_id, organization_id, lock=True)
        if case.status not in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION):
            raise reception_difference_error("ReceptionDifferenceCaseNotEditable", "El caso no es editable en su estado actual.", 409)
        allowed_fields = {"supplier_snapshot", "carrier_snapshot", "severity"}
        for key, value in fields.items():
            if key in allowed_fields:
                setattr(case, key, value)
        case.row_version += 1
        self.db.flush()
        self._emit(case, principal, event_code="logistics.reception_difference.case_updated")
        return case

    def transition_case(self, case_id: UUID, target_status: str, principal: LogisticsPrincipal, reason: str | None = None) -> ReceptionDifferenceCaseModel:
        from app.modules.logistics.auth_dependencies import resolve_organization_id
        organization_id = resolve_organization_id(principal)
        case = self._get_case(case_id, organization_id, lock=True)
        require_case_transition(case.status, target_status)
        timestamp = now()
        case.status = target_status
        case.row_version += 1

        if target_status == CaseStatus.SUBMITTED_FOR_REVIEW:
            case.submitted_at = timestamp
            case.submitted_by = principal.user_id
        elif target_status == CaseStatus.APPROVED:
            case.approved_at = timestamp
            case.approved_by = principal.user_id
        elif target_status == CaseStatus.ISSUED:
            case.issued_at = timestamp
            case.issued_by = principal.user_id
        elif target_status == CaseStatus.ACKNOWLEDGED:
            case.acknowledged_at = timestamp
        elif target_status == CaseStatus.DISPUTED:
            case.disputed_at = timestamp
        elif target_status == CaseStatus.CLOSED:
            case.closed_at = timestamp
        elif target_status == CaseStatus.CANCELLED:
            case.cancelled_at = timestamp
            case.cancellation_reason = reason

        self.db.flush()
        self._emit(case, principal, f"logistics.reception_difference.case_{target_status.lower()}", reason=reason)
        return case

    def validate_case(self, case_id: UUID, organization_id_or_principal) -> dict:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        case = self._get_case(case_id, organization_id)
        errors: list[str] = []
        warnings: list[str] = []

        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id)
        ))
        if not items:
            errors.append("NO_ITEMS")

        open_items = [i for i in items if i.status in ("OPEN", "EVIDENCE_PENDING", "RESPONSIBILITY_PENDING", "READY_FOR_REVIEW")]
        if open_items:
            errors.append("OPEN_ITEMS_REMAINING")

        critical_items = [i for i in items if i.severity == Severity.CRITICAL]
        if critical_items and case.status != CaseStatus.UNDER_REVIEW:
            warnings.append("CRITICAL_ITEMS_PRESENT")

        evidence_count = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ) or 0
        if evidence_count == 0:
            warnings.append("NO_EVIDENCE_LINKED")

        has_responsible = self.db.scalar(
            select(func.count()).select_from(ReceptionDifferenceResponsiblePartyModel).where(
                ReceptionDifferenceResponsiblePartyModel.difference_case_id == case.id,
            )
        ) or 0
        if has_responsible == 0:
            warnings.append("NO_RESPONSIBILITY_ASSIGNED")

        result = {
            "case_id": str(case.id),
            "status": case.status,
            "is_valid": not errors,
            "blocking_errors": errors,
            "warnings": warnings,
            "item_count": len(items),
            "open_item_count": len(open_items),
            "critical_item_count": len(critical_items),
            "evidence_count": evidence_count,
            "responsible_party_count": has_responsible,
            "validation_hash": canonical_hash_diff({"case_id": str(case.id), "errors": errors, "warnings": warnings}),
        }
        return result

    def get_capabilities(self, case_id: UUID, organization_id_or_principal) -> dict:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        case = self._get_case(case_id, organization_id)
        status = CaseStatus(case.status)
        from ...domain.enums import CASE_TRANSITIONS
        allowed = CASE_TRANSITIONS.get(status, set())
        return {
            "case_id": str(case.id),
            "current_status": case.status,
            "allowed_transitions": [s.value for s in allowed],
            "can_add_items": case.status in (CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION),
            "can_add_evidence": case.status not in (CaseStatus.CLOSED, CaseStatus.CANCELLED, CaseStatus.SUPERSEDED),
            "can_assign_responsibility": case.status not in (CaseStatus.CLOSED, CaseStatus.CANCELLED, CaseStatus.SUPERSEDED),
            "can_submit": case.status in (CaseStatus.UNDER_PREPARATION, CaseStatus.PENDING_EVIDENCE, CaseStatus.PENDING_RESPONSIBILITY),
            "can_review": case.status in (CaseStatus.SUBMITTED_FOR_REVIEW,),
            "can_approve": case.status in (CaseStatus.READY_FOR_APPROVAL,),
            "can_issue": case.status in (CaseStatus.APPROVED,),
            "is_terminal": status in (CaseStatus.CLOSED, CaseStatus.CANCELLED, CaseStatus.SUPERSEDED),
        }

    def get_history(self, case_id: UUID, organization_id_or_principal) -> dict:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        case = self._get_case(case_id, organization_id)
        revisions = list(self.db.scalars(
            select(ReceptionDifferenceCaseRevisionModel)
            .where(ReceptionDifferenceCaseRevisionModel.difference_case_id == case.id)
            .order_by(ReceptionDifferenceCaseRevisionModel.revision_number)
        ))
        return {
            "case_id": str(case.id),
            "case_code": case.case_code,
            "current_revision_number": case.current_revision_number,
            "revisions": [
                {
                    "revision_id": str(r.id),
                    "revision_number": r.revision_number,
                    "status": r.status,
                    "created_by": str(r.created_by),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                    "frozen_at": r.frozen_at.isoformat() if r.frozen_at else None,
                    "content_hash": r.content_hash,
                }
                for r in revisions
            ],
            "status_transitions": [
                {"status": case.status, "at": case.created_at.isoformat() if case.created_at else None},
            ],
        }

    def get_integrity(self, case_id: UUID, organization_id_or_principal) -> dict:
        from app.modules.logistics.principal import LogisticsPrincipal
        if isinstance(organization_id_or_principal, LogisticsPrincipal):
            from app.modules.logistics.auth_dependencies import resolve_organization_id
            organization_id = resolve_organization_id(organization_id_or_principal)
        else:
            organization_id = organization_id_or_principal
        case = self._get_case(case_id, organization_id)
        revision = self.db.get(ReceptionDifferenceCaseRevisionModel, case.active_revision_id) if case.active_revision_id else None
        if not revision:
            return {"status": "NO_REVISION", "case_id": str(case.id)}

        snapshot = {
            "items": jsonable_encoder([
                {c.name: getattr(i, c.name) for c in ReceptionDifferenceItemModel.__table__.columns}
                for i in self.db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id))
            ]),
            "evidence": jsonable_encoder([
                {c.name: getattr(e, c.name) for c in ReceptionDifferenceEvidenceLinkModel.__table__.columns}
                for e in self.db.scalars(select(ReceptionDifferenceEvidenceLinkModel).where(ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id))
            ]),
        }
        calculated_hash = canonical_hash_diff(snapshot)
        stored_hash = revision.content_hash
        return {
            "case_id": str(case.id),
            "revision_id": str(revision.id),
            "status": "VALID" if not stored_hash or stored_hash == calculated_hash else "MISMATCH",
            "calculated_hash": calculated_hash,
            "stored_hash": stored_hash,
        }
