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

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class ReceptionDifferenceEvidenceService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_EVIDENCE",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:evidence:{case.id}:{event_code}:{event_id}",
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
            resource_type="reception_difference_evidence",
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

    def link_evidence(
        self,
        case_id: UUID,
        item_id: UUID | None,
        file_asset_id: UUID,
        file_version_id: UUID | None,
        evidence_type: str,
        classification: str,
        description: str | None,
        captured_at: datetime | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceEvidenceLinkModel:
        case = self._get_case(case_id, principal.organization_id)

        if item_id:
            item = self.db.scalar(select(ReceptionDifferenceItemModel).where(
                ReceptionDifferenceItemModel.id == item_id,
                ReceptionDifferenceItemModel.difference_case_id == case_id,
            ))
            if not item:
                raise reception_difference_error("ReceptionDifferenceItemNotFound", "Ítem no encontrado.", 404)

        link = ReceptionDifferenceEvidenceLinkModel(
            id=uuid4(),
            difference_case_id=case_id,
            difference_item_id=item_id,
            file_asset_id=file_asset_id,
            file_version_id=file_version_id,
            evidence_type=evidence_type,
            source_type="UPLOAD",
            classification=classification,
            description=description,
            captured_at=captured_at,
            linked_at=now(),
            linked_by=principal.user_id,
            status="ACTIVE",
        )
        self.db.add(link)
        self.db.flush()

        case.evidence_count += 1
        case.row_version += 1
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.evidence_linked", metadata={"evidence_link_id": str(link.id), "item_id": str(item_id) if item_id else None})
        return link

    def list_evidence(self, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceEvidenceLinkModel]:
        self._get_case(case_id, organization_id)
        return list(self.db.scalars(
            select(ReceptionDifferenceEvidenceLinkModel)
            .where(ReceptionDifferenceEvidenceLinkModel.difference_case_id == case_id, ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE")
            .order_by(ReceptionDifferenceEvidenceLinkModel.created_at)
        ))

    def list_item_evidence(self, item_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceEvidenceLinkModel]:
        return list(self.db.scalars(
            select(ReceptionDifferenceEvidenceLinkModel)
            .where(ReceptionDifferenceEvidenceLinkModel.difference_item_id == item_id, ReceptionDifferenceEvidenceLinkModel.status == "ACTIVE")
            .order_by(ReceptionDifferenceEvidenceLinkModel.created_at)
        ))

    def archive_evidence(self, evidence_link_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> ReceptionDifferenceEvidenceLinkModel:
        link = self.db.scalar(select(ReceptionDifferenceEvidenceLinkModel).join(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceEvidenceLinkModel.id == evidence_link_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not link:
            raise reception_difference_error("ReceptionDifferenceEvidenceUnavailable", "Enlace de evidencia no encontrado.", 404)
        link.status = "ARCHIVED"
        self.db.flush()

        case = self._get_case(link.difference_case_id, organization_id)
        case.evidence_count = max(case.evidence_count - 1, 0)
        case.row_version += 1
        self.db.flush()
        return link
