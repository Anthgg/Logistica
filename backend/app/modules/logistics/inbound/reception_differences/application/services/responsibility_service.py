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

from ...domain.enums import ResponsibilityStatus, ResponsibilityRole
from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceResponsiblePartyModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def actor(principal: LogisticsPrincipal) -> dict[str, str]:
    return {"user_id": str(principal.user_id), "display_name": principal.full_name, "email": principal.email}


class ReceptionDifferenceResponsibilityService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal, event_code: str, *, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_RESPONSIBILITY",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:responsibility:{case.id}:{event_code}:{event_id}",
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
            resource_type="reception_difference_responsibility",
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

    def _get_responsible(self, responsibility_id: UUID, organization_id: UUID) -> ReceptionDifferenceResponsiblePartyModel:
        party = self.db.scalar(select(ReceptionDifferenceResponsiblePartyModel).join(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceResponsiblePartyModel.id == responsibility_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not party:
            raise reception_difference_error("ReceptionDifferenceResponsibilityInvalid", "Responsable no encontrado.", 404)
        return party

    def propose_responsible(
        self,
        case_id: UUID,
        item_id: UUID | None,
        party_type: str,
        business_partner_id: UUID | None,
        user_id: UUID | None,
        responsibility_role: str,
        notes: str | None,
        allocation_percentage: float | None,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceResponsiblePartyModel:
        case = self._get_case(case_id, principal.organization_id)

        if item_id:
            item = self.db.scalar(select(ReceptionDifferenceItemModel).where(
                ReceptionDifferenceItemModel.id == item_id,
                ReceptionDifferenceItemModel.difference_case_id == case_id,
            ))
            if not item:
                raise reception_difference_error("ReceptionDifferenceItemNotFound", "Ítem no encontrado.", 404)

        from decimal import Decimal as D
        alloc = D(str(allocation_percentage)) if allocation_percentage is not None else None

        party = ReceptionDifferenceResponsiblePartyModel(
            id=uuid4(),
            difference_case_id=case_id,
            difference_item_id=item_id,
            party_type=party_type,
            business_partner_id=business_partner_id,
            user_id=user_id,
            responsible_snapshot=actor(principal),
            responsibility_role=responsibility_role,
            responsibility_status=ResponsibilityStatus.PROPOSED,
            proposed_by=principal.user_id,
            proposed_at=now(),
            allocation_percentage=alloc,
            notes=notes,
        )
        self.db.add(party)
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.responsibility_proposed", metadata={"responsibility_id": str(party.id), "party_type": party_type})
        return party

    def review_responsible(self, responsibility_id: UUID, organization_id: UUID, principal: LogisticsPrincipal, review_notes: str | None = None) -> ReceptionDifferenceResponsiblePartyModel:
        party = self._get_responsible(responsibility_id, organization_id)
        party.responsibility_status = ResponsibilityStatus.ASSIGNED_INTERNAL
        party.reviewed_by = principal.user_id
        party.reviewed_at = now()
        self.db.flush()

        case = self._get_case(party.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.responsibility_reviewed", metadata={"responsibility_id": str(responsibility_id)})
        return party

    def acknowledge_responsible(self, responsibility_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> ReceptionDifferenceResponsiblePartyModel:
        party = self._get_responsible(responsibility_id, organization_id)
        party.responsibility_status = ResponsibilityStatus.ACKNOWLEDGED
        party.acknowledged_by = principal.user_id
        party.acknowledged_at = now()
        self.db.flush()

        case = self._get_case(party.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.responsibility_acknowledged", metadata={"responsibility_id": str(responsibility_id)})
        return party

    def dispute_responsible(self, responsibility_id: UUID, organization_id: UUID, dispute_reason: str, principal: LogisticsPrincipal) -> ReceptionDifferenceResponsiblePartyModel:
        party = self._get_responsible(responsibility_id, organization_id)
        party.responsibility_status = ResponsibilityStatus.DISPUTED
        party.disputed_by = principal.user_id
        party.disputed_at = now()
        party.dispute_reason = dispute_reason
        self.db.flush()

        case = self._get_case(party.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.responsibility_disputed", metadata={"responsibility_id": str(responsibility_id), "dispute_reason": dispute_reason})
        return party

    def mark_undetermined(self, responsibility_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> ReceptionDifferenceResponsiblePartyModel:
        party = self._get_responsible(responsibility_id, organization_id)
        party.responsibility_status = ResponsibilityStatus.UNDETERMINED
        self.db.flush()

        case = self._get_case(party.difference_case_id, organization_id)
        self._emit(case, principal, "logistics.reception_difference.responsibility_undetermined", metadata={"responsibility_id": str(responsibility_id)})
        return party

    def list_responsible_parties(self, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceResponsiblePartyModel]:
        self._get_case(case_id, organization_id)
        return list(self.db.scalars(
            select(ReceptionDifferenceResponsiblePartyModel)
            .where(ReceptionDifferenceResponsiblePartyModel.difference_case_id == case_id)
            .order_by(ReceptionDifferenceResponsiblePartyModel.created_at)
        ))
