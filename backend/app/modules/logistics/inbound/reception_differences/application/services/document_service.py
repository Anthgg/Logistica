from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ...domain.enums import CaseStatus
from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceDocumentPackageModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceResponsiblePartyModel,
    ReceptionDifferenceReviewModel,
    ReceptionDifferenceApprovalModel,
    ReceptionDifferenceAcknowledgementModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class ReceptionDifferenceDocumentService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_DOCUMENT",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:doc:{case.id}:{event_code}:{event_id}",
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
            resource_type="reception_difference_document",
            resource_id=str(event_id),
            action=event_code.rsplit(".", 1)[-1],
            metadata=metadata,
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

    def _build_preview(self, case: ReceptionDifferenceCaseModel) -> dict:
        items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id)
        ))
        evidence = list(self.db.scalars(
            select(ReceptionDifferenceEvidenceLinkModel).where(
                ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id,
                ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE",
            )
        ))
        responsibilities = list(self.db.scalars(
            select(ReceptionDifferenceResponsiblePartyModel).where(ReceptionDifferenceResponsiblePartyModel.difference_case_id == case.id)
        ))
        reviews = list(self.db.scalars(
            select(ReceptionDifferenceReviewModel).where(ReceptionDifferenceReviewModel.difference_case_id == case.id)
        ))
        approvals = list(self.db.scalars(
            select(ReceptionDifferenceApprovalModel).where(ReceptionDifferenceApprovalModel.difference_case_id == case.id)
        ))
        acknowledgements = list(self.db.scalars(
            select(ReceptionDifferenceAcknowledgementModel).where(ReceptionDifferenceAcknowledgementModel.difference_case_id == case.id)
        ))
        return {
            "case_id": str(case.id),
            "case_code": case.case_code,
            "status": case.status,
            "warehouse_id": str(case.warehouse_id),
            "supplier_snapshot": case.supplier_snapshot,
            "carrier_snapshot": case.carrier_snapshot,
            "item_count": len(items),
            "items": [{"item_number": i.item_number, "difference_type": i.difference_type, "category": i.category, "severity": i.severity, "title": i.title} for i in items],
            "evidence_count": len(evidence),
            "responsible_party_count": len(responsibilities),
            "review_count": len(reviews),
            "approval_count": len(approvals),
            "acknowledgement_count": len(acknowledgements),
            "content_hash": canonical_hash_diff({"case_id": str(case.id), "items": [i.item_number for i in items]}),
        }

    def preview(self, case_id: UUID, organization_id: UUID) -> dict:
        case = self._get_case(case_id, organization_id)
        preview = self._build_preview(case)
        preview["document_code"] = None
        return preview

    def issue_document(self, case_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> dict:
        case = self._get_case(case_id, organization_id)
        if case.document_instance_id:
            raise reception_difference_error("ReceptionDifferenceAlreadyIssued", "El documento ya fue emitido.", 409)

        preview = self._build_preview(case)
        document_instance_id = uuid4()
        case.document_instance_id = document_instance_id
        case.issued_at = now()
        case.issued_by = principal.user_id
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.document_issued", metadata={"document_instance_id": str(document_instance_id)})
        return {**preview, "document_instance_id": str(document_instance_id), "issued_at": case.issued_at.isoformat()}

    def cancel_document(self, case_id: UUID, organization_id: UUID, reason: str, principal: LogisticsPrincipal) -> dict:
        case = self._get_case(case_id, organization_id)
        if not case.document_instance_id:
            raise reception_difference_error("ReceptionDifferenceDocumentIssueFailed", "No hay documento emitido para cancelar.", 409)

        previous_doc_id = case.document_instance_id
        case.document_instance_id = None
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.document_cancelled", metadata={"previous_document_instance_id": str(previous_doc_id), "reason": reason})
        return {"case_id": str(case.id), "cancelled_document_instance_id": str(previous_doc_id), "reason": reason}

    def reprint(self, case_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> dict:
        case = self._get_case(case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.document_reprinted")
        return self._build_preview(case)

    def create_package(self, case_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> dict:
        case = self._get_case(case_id, organization_id)
        package = ReceptionDifferenceDocumentPackageModel(
            id=uuid4(),
            difference_case_id=case_id,
            package_type="DIF_PACKAGE",
            status="PENDING",
            created_by=principal.user_id,
        )
        self.db.add(package)
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.document_package_created", metadata={"package_id": str(package.id)})
        return {"package_id": str(package.id), "status": package.status}
