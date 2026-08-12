"""Shared transaction, audit, outbox, hashing, and server-clock helpers."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import (
    get_idempotent_response,
    save_idempotent_response,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockOperationalEventModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def server_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_code(value: str) -> str:
    return "".join(character for character in value.upper().strip() if character.isalnum())


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_payload(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def actor_snapshot(principal: LogisticsPrincipal) -> dict[str, str]:
    return {
        "user_id": str(principal.user_id),
        "display_name": principal.full_name,
        "email": principal.email,
    }


class DockIdempotencyService:
    @staticmethod
    def replay(
        db: Session,
        organization_id: UUID,
        operation: str,
        key: str | None,
        payload: dict,
    ) -> dict | None:
        return get_idempotent_response(db, organization_id, operation, key, payload)

    @staticmethod
    def save(
        db: Session,
        principal: LogisticsPrincipal,
        organization_id: UUID,
        operation: str,
        key: str | None,
        payload: dict,
        response: dict,
    ) -> None:
        save_idempotent_response(
            db,
            organization_id,
            principal.user_id,
            operation,
            key,
            payload,
            response,
        )


class DockMasterEventService:
    """Transactional outbox and unified audit for dock master-data changes."""

    def __init__(self, db: Session):
        self.db = db

    def append(
        self,
        *,
        dock: object,
        principal: LogisticsPrincipal,
        event_type: str,
        audit_code: str,
        reason: str | None = None,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        now = server_now()
        self.db.add(
            ArrivalNoticeOutboxEventModel(
                id=uuid4(),
                organization_id=dock.organization_id,
                aggregate_type="WAREHOUSE_DOCK",
                aggregate_id=dock.id,
                event_type=event_type,
                payload={"dock_id": str(dock.id), "warehouse_id": str(dock.warehouse_id), "occurred_at": now.isoformat()},
                deduplication_key=f"dock-master:{dock.id}:{event_type}:{uuid4()}",
                status="PENDING",
            )
        )
        AuditService().write_event(
            self.db,
            AuditEventCommand(
                event_code=audit_code,
                actor_user_id=principal.user_id,
                actor_display_name=principal.full_name,
                actor_role_codes=principal.role_codes,
                session_id=principal.session_id,
                device_id=principal.device_id,
                authentication_level=principal.authentication_level,
                risk_score=principal.risk_score,
                correlation_id=principal.correlation_id,
                ip_address=principal.ip_address,
                user_agent=principal.user_agent,
                organization_id=dock.organization_id,
                warehouse_id=dock.warehouse_id,
                resource_type="warehouse_dock",
                resource_id=str(dock.id),
                action=event_type.lower(),
                reason_text=reason,
                previous_data=previous_data,
                new_data=new_data,
                source_module="logistics.inbound.dock_operations",
                source_service=self.__class__.__name__,
            ),
        )


class UnloadingOperationalEventService:
    """Append-only event stream plus transactional outbox and unified audit."""

    def __init__(self, db: Session):
        self.db = db

    def append(
        self,
        *,
        principal: LogisticsPrincipal,
        organization_id: UUID,
        warehouse_id: UUID,
        gate_check_in_id: UUID,
        event_type: str,
        audit_code: str,
        dock_id: UUID | None = None,
        assignment_id: UUID | None = None,
        operation_id: UUID | None = None,
        payload: dict | None = None,
        reason: str | None = None,
        previous_status: str | None = None,
        new_status: str | None = None,
    ) -> DockOperationalEventModel:
        now = server_now()
        latest = self.db.scalar(
            select(DockOperationalEventModel)
            .where(DockOperationalEventModel.gate_check_in_id == gate_check_in_id)
            .order_by(DockOperationalEventModel.sequence_number.desc())
            .limit(1)
            .with_for_update()
        )
        sequence = 1 if latest is None else latest.sequence_number + 1
        summary = payload or {}
        digest_input = {
            "schema_version": "1.0.0",
            "organization_id": organization_id,
            "warehouse_id": warehouse_id,
            "dock_id": dock_id,
            "gate_check_in_id": gate_check_in_id,
            "dock_assignment_id": assignment_id,
            "unloading_operation_id": operation_id,
            "sequence_number": sequence,
            "event_type": event_type,
            "event_at": now,
            "actor_user_id": principal.user_id,
            "payload_summary": summary,
            "previous_event_hash": latest.event_hash if latest else None,
        }
        event = DockOperationalEventModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            dock_id=dock_id,
            gate_check_in_id=gate_check_in_id,
            dock_assignment_id=assignment_id,
            unloading_operation_id=operation_id,
            sequence_number=sequence,
            event_type=event_type,
            event_at=now,
            actor_user_id=principal.user_id,
            actor_snapshot=actor_snapshot(principal),
            source="BACKEND_COMMAND",
            payload_summary=summary,
            previous_event_hash=latest.event_hash if latest else None,
            event_hash=sha256_payload(digest_input),
            correlation_id=principal.correlation_id,
        )
        self.db.add(event)
        self.db.flush()

        dedupe = f"dock:{gate_check_in_id}:{sequence}:{event_type}"
        self.db.add(
            ArrivalNoticeOutboxEventModel(
                id=uuid4(),
                organization_id=organization_id,
                aggregate_type="DOCK_OPERATION",
                aggregate_id=operation_id or assignment_id or gate_check_in_id,
                event_type=event_type,
                payload={
                    "event_id": str(event.id),
                    "gate_check_in_id": str(gate_check_in_id),
                    "dock_assignment_id": str(assignment_id) if assignment_id else None,
                    "unloading_operation_id": str(operation_id) if operation_id else None,
                    "occurred_at": now.isoformat(),
                },
                deduplication_key=dedupe,
                status="PENDING",
            )
        )

        AuditService().write_event(
            self.db,
            AuditEventCommand(
                event_code=audit_code,
                actor_user_id=principal.user_id,
                actor_display_name=principal.full_name,
                actor_role_codes=principal.role_codes,
                session_id=principal.session_id,
                device_id=principal.device_id,
                authentication_level=principal.authentication_level,
                risk_score=principal.risk_score,
                correlation_id=principal.correlation_id,
                ip_address=principal.ip_address,
                user_agent=principal.user_agent,
                organization_id=organization_id,
                warehouse_id=warehouse_id,
                resource_type="dock_operation",
                resource_id=str(operation_id or assignment_id or gate_check_in_id),
                action=event_type.lower(),
                reason_text=reason,
                previous_data={"status": previous_status} if previous_status else None,
                new_data={"status": new_status, **summary} if new_status else summary,
                source_module="logistics.inbound.dock_operations",
                source_service=self.__class__.__name__,
            ),
        )
        return event

    def verify_chain(self, gate_check_in_id: UUID) -> tuple[bool, list[str], str | None]:
        rows = list(
            self.db.scalars(
                select(DockOperationalEventModel)
                .where(DockOperationalEventModel.gate_check_in_id == gate_check_in_id)
                .order_by(DockOperationalEventModel.sequence_number)
            )
        )
        alerts: list[str] = []
        previous_hash: str | None = None
        expected_sequence = 1
        for row in rows:
            if row.sequence_number != expected_sequence:
                alerts.append("EVENT_SEQUENCE_GAP")
            if row.previous_event_hash != previous_hash:
                alerts.append("EVENT_CHAIN_MISMATCH")
            previous_hash = row.event_hash
            expected_sequence += 1
        return not alerts, alerts, previous_hash


def active_count(db: Session, model: type, *conditions: object) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)
