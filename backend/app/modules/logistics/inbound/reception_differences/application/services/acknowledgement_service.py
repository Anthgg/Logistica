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

from ...domain.enums import AcknowledgementType
from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceAcknowledgementModel,
    ReceptionDifferenceCaseModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class ReceptionDifferenceAcknowledgementService:
    def __init__(self, db: Session):
        self.db = db

    def _emit(self, case: ReceptionDifferenceCaseModel, principal: LogisticsPrincipal | None, event_code: str, *, metadata: dict | None = None) -> None:
        event_id = uuid4()
        timestamp = now()
        self.db.add(ArrivalNoticeOutboxEventModel(
            id=event_id,
            organization_id=case.organization_id,
            aggregate_type="RECEPTION_DIFFERENCE_ACKNOWLEDGEMENT",
            aggregate_id=event_id,
            event_type=event_code,
            payload={
                "case_id": str(case.id),
                "occurred_at": timestamp.isoformat(),
                **(metadata or {}),
            },
            deduplication_key=f"phase040:ack:{case.id}:{event_code}:{event_id}",
            status="PENDING",
        ))
        if principal:
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
                resource_type="reception_difference_acknowledgement",
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

    def create_acknowledgement(
        self,
        case_id: UUID,
        party_type: str,
        business_partner_id: UUID | None,
        acknowledgement_type: str,
        statement: str | None,
        source_channel: str,
        principal: LogisticsPrincipal,
    ) -> ReceptionDifferenceAcknowledgementModel:
        case = self._get_case(case_id, principal.organization_id)

        AcknowledgementType(acknowledgement_type)

        ack = ReceptionDifferenceAcknowledgementModel(
            id=uuid4(),
            difference_case_id=case_id,
            party_type=party_type,
            business_partner_id=business_partner_id,
            acknowledgement_type=acknowledgement_type,
            statement=statement,
            status="ACTIVE",
            acknowledged_at=now(),
            source_channel=source_channel,
        )
        self.db.add(ack)
        self.db.flush()

        self._emit(case, principal, "logistics.reception_difference.acknowledgement_created", metadata={"acknowledgement_id": str(ack.id), "party_type": party_type})
        return ack

    def list_acknowledgements(self, case_id: UUID, organization_id: UUID) -> list[ReceptionDifferenceAcknowledgementModel]:
        self._get_case(case_id, organization_id)
        return list(self.db.scalars(
            select(ReceptionDifferenceAcknowledgementModel)
            .where(ReceptionDifferenceAcknowledgementModel.difference_case_id == case_id)
            .order_by(ReceptionDifferenceAcknowledgementModel.created_at)
        ))
