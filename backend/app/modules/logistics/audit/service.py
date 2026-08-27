"""Audit service — unified event writing, integrity hashing, query."""

from __future__ import annotations

import builtins
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.modules.logistics.audit.catalog import (
    EVENT_CODE_MAP,
    EventCategory,
    EventSeverity,
    is_valid_event_code,
)
from app.modules.logistics.audit.models_event import LogisticsAuditEvent
from app.modules.logistics.audit.sanitizer import (
    compute_changed_fields,
    sanitize_for_audit,
)


@dataclass
class AuditEventCommand:
    event_code: str
    # Compatibility aliases used by the master-data modules developed before
    # the unified audit contract was finalized.  The catalog remains the
    # authority for category and default severity.
    category: str | None = None
    description: str | None = None
    payload: dict | None = None
    actor_user_id: UUID | None = None
    actor_display_name: str | None = None
    actor_role_codes: list[str] | None = None
    actor_type: str = "user"
    action: str | None = None
    result: str = "success"
    severity: str = "info"
    resource_type: str | None = None
    resource_id: str | None = None
    resource_code: str | None = None
    parent_resource_type: str | None = None
    parent_resource_id: str | None = None
    organization_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    session_id: UUID | None = None
    device_id: UUID | None = None
    authentication_level: str | None = None
    risk_score: float | None = None
    step_up_required: bool = False
    step_up_result: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    method: str | None = None
    endpoint: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    origin: str | None = None
    reason_code: str | None = None
    reason_text: str | None = None
    previous_data: dict | None = None
    new_data: dict | None = None
    metadata: dict | None = None
    source_module: str | None = None
    source_service: str | None = None


def _compute_hash(event: LogisticsAuditEvent) -> str:
    payload = {
        "id": str(event.id),
        "event_code": event.event_code,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else "",
        "actor_user_id": str(event.actor_user_id) if event.actor_user_id else "",
        "resource_type": event.resource_type or "",
        "resource_id": event.resource_id or "",
        "result": event.result,
        "previous_data": event.previous_data,
        "new_data": event.new_data,
    }
    dumped = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


class AuditService:
    def write_event(self, db: Session, command: AuditEventCommand) -> LogisticsAuditEvent:
        if not is_valid_event_code(command.event_code):
            raise ApplicationError("INVALID_EVENT_CODE", f"Código de evento no catalogado: {command.event_code}", 400)

        meta = EVENT_CODE_MAP[command.event_code]
        category = meta.get("category", EventCategory.SYSTEM)
        sev = command.severity or meta.get("default_severity", EventSeverity.INFO)

        sanitized_prev = sanitize_for_audit(command.previous_data)
        sanitized_new = sanitize_for_audit(command.new_data)
        changed = compute_changed_fields(sanitized_prev, sanitized_new)

        role_snapshot = ",".join(command.actor_role_codes) if command.actor_role_codes else None

        event = LogisticsAuditEvent(
            id=uuid4(),
            event_code=command.event_code,
            event_category=category,
            event_version="1.0.0",
            actor_type=command.actor_type,
            actor_user_id=command.actor_user_id,
            actor_display_name_snapshot=command.actor_display_name,
            actor_role_codes_snapshot=role_snapshot,
            session_id=command.session_id,
            device_id=command.device_id,
            authentication_level=command.authentication_level,
            risk_score=command.risk_score,
            step_up_required=command.step_up_required,
            step_up_result=command.step_up_result,
            request_id=command.request_id,
            correlation_id=command.correlation_id,
            method=command.method,
            endpoint=command.endpoint,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
            origin=command.origin,
            occurred_at=utc_now(),
            action=command.action,
            result=command.result,
            severity=sev,
            resource_type=command.resource_type,
            resource_id=command.resource_id,
            resource_code=command.resource_code,
            parent_resource_type=command.parent_resource_type,
            parent_resource_id=command.parent_resource_id,
            organization_id=command.organization_id,
            branch_id=command.branch_id,
            warehouse_id=command.warehouse_id,
            reason_code=command.reason_code,
            reason_text=command.reason_text or command.description,
            previous_data=sanitized_prev,
            new_data=sanitized_new,
            changed_fields=changed,
            metadata_=command.metadata if command.metadata is not None else command.payload,
            source_module=command.source_module,
            source_service=command.source_service,
            schema_version="1.0.0",
        )

        event.event_hash = _compute_hash(event)
        db.add(event)
        db.flush()
        return event

    def record_event(
        self,
        db: Session,
        command: AuditEventCommand,
    ) -> LogisticsAuditEvent:
        """Compatibility alias for Phase 025 partner services."""
        return self.write_event(db, command)

    def log_event(
        self,
        db: Session,
        command: AuditEventCommand,
    ) -> LogisticsAuditEvent:
        """Compatibility alias for Phase 026 RUC services."""
        return self.write_event(db, command)

    def get_by_id(self, db: Session, event_id: UUID) -> LogisticsAuditEvent | None:
        return db.get(LogisticsAuditEvent, event_id)

    def _build_filters(
        self,
        *,
        event_code: str | None = None,
        event_category: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        result: str | None = None,
        action: str | None = None,
        actor_user_id: UUID | None = None,
        organization_id: UUID | None = None,
        branch_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        allowed_org_ids: list[UUID] | None = None,
    ) -> list[Any]:
        cat = event_category or category
        filters = []
        if event_code:
            filters.append(LogisticsAuditEvent.event_code == event_code)
        if cat:
            filters.append(LogisticsAuditEvent.event_category == cat)
        if severity:
            filters.append(LogisticsAuditEvent.severity == severity)
        if result:
            filters.append(LogisticsAuditEvent.result == result)
        if action:
            filters.append(LogisticsAuditEvent.action == action)
        if actor_user_id:
            filters.append(LogisticsAuditEvent.actor_user_id == actor_user_id)
        if branch_id:
            filters.append(LogisticsAuditEvent.branch_id == branch_id)
        if warehouse_id:
            filters.append(LogisticsAuditEvent.warehouse_id == warehouse_id)
        if resource_type:
            filters.append(LogisticsAuditEvent.resource_type == resource_type)
        if resource_id:
            filters.append(LogisticsAuditEvent.resource_id == resource_id)
        if correlation_id:
            filters.append(LogisticsAuditEvent.correlation_id == correlation_id)
        if request_id:
            filters.append(LogisticsAuditEvent.request_id == request_id)
        if session_id:
            filters.append(LogisticsAuditEvent.session_id == session_id)
        if date_from:
            filters.append(LogisticsAuditEvent.occurred_at >= date_from)
        if date_to:
            filters.append(LogisticsAuditEvent.occurred_at <= date_to)

        # Tenant isolation
        if allowed_org_ids is not None:
            if organization_id is not None:
                if organization_id not in allowed_org_ids:
                    raise ApplicationError("FORBIDDEN", "No tiene acceso a esta organización.", 403)
                filters.append(LogisticsAuditEvent.organization_id == organization_id)
            else:
                filters.append(
                    or_(
                        LogisticsAuditEvent.organization_id.in_(allowed_org_ids),
                        LogisticsAuditEvent.organization_id.is_(None),
                    )
                )
        elif organization_id is not None:
            filters.append(LogisticsAuditEvent.organization_id == organization_id)

        # General text search
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    LogisticsAuditEvent.event_code.ilike(term),
                    LogisticsAuditEvent.resource_id.ilike(term),
                    LogisticsAuditEvent.actor_display_name_snapshot.ilike(term),
                    LogisticsAuditEvent.reason_text.ilike(term),
                    LogisticsAuditEvent.action.ilike(term),
                )
            )

        return filters

    def list(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        event_code: str | None = None,
        event_category: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        result: str | None = None,
        action: str | None = None,
        actor_user_id: UUID | None = None,
        organization_id: UUID | None = None,
        branch_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        allowed_org_ids: list[UUID] | None = None,
    ) -> tuple[builtins.list[LogisticsAuditEvent], int]:
        filters = self._build_filters(
            event_code=event_code,
            event_category=event_category,
            category=category,
            severity=severity,
            result=result,
            action=action,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            request_id=request_id,
            session_id=session_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            allowed_org_ids=allowed_org_ids,
        )

        total = db.scalar(select(func.count()).select_from(LogisticsAuditEvent).where(*filters)) or 0
        items = list(
            db.scalars(
                select(LogisticsAuditEvent)
                .where(*filters)
                .order_by(LogisticsAuditEvent.occurred_at.desc(), LogisticsAuditEvent.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def export_csv(
        self,
        db: Session,
        *,
        include_sensitive_ip: bool = False,
        max_rows: int = 10000,
        event_code: str | None = None,
        event_category: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        result: str | None = None,
        action: str | None = None,
        actor_user_id: UUID | None = None,
        organization_id: UUID | None = None,
        branch_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        allowed_org_ids: list[UUID] | None = None,
    ) -> tuple[str, int]:
        filters = self._build_filters(
            event_code=event_code,
            event_category=event_category,
            category=category,
            severity=severity,
            result=result,
            action=action,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            request_id=request_id,
            session_id=session_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            allowed_org_ids=allowed_org_ids,
        )

        query = (
            select(LogisticsAuditEvent)
            .where(*filters)
            .order_by(LogisticsAuditEvent.occurred_at.desc(), LogisticsAuditEvent.id.desc())
            .limit(max_rows)
        )
        items = list(db.scalars(query))

        output = io.StringIO()
        # Write UTF-8 BOM for automatic Excel detection
        output.write("\ufeff")
        writer = csv.writer(output, dialect="excel")
        writer.writerow([
            "ID",
            "Fecha/Hora (UTC)",
            "Código de Evento",
            "Categoría",
            "Severidad",
            "Resultado",
            "Acción",
            "Recurso",
            "ID Recurso",
            "Código Recurso",
            "Actor ID",
            "Actor",
            "Organización ID",
            "Sede ID",
            "Almacén ID",
            "IP",
            "Motivo",
            "Campos Modificados",
        ])

        for event in items:
            ip_val = event.ip_address if include_sensitive_ip else ("[REDACTED]" if event.ip_address else "")
            changed_val = ", ".join(event.changed_fields) if event.changed_fields else ""
            date_val = event.occurred_at.isoformat() if event.occurred_at else ""
            writer.writerow([
                str(event.id),
                date_val,
                event.event_code or "",
                event.event_category or "",
                event.severity or "",
                event.result or "",
                event.action or "",
                event.resource_type or "",
                event.resource_id or "",
                event.resource_code or "",
                str(event.actor_user_id) if event.actor_user_id else "",
                event.actor_display_name_snapshot or "",
                str(event.organization_id) if event.organization_id else "",
                str(event.branch_id) if event.branch_id else "",
                str(event.warehouse_id) if event.warehouse_id else "",
                ip_val,
                event.reason_text or "",
                changed_val,
            ])

        return output.getvalue(), len(items)

    def list_by_resource(self, db: Session, resource_type: str, resource_id: str, *, page: int = 1, page_size: int = 20) -> tuple[builtins.list[LogisticsAuditEvent], int]:
        return self.list(db, page=page, page_size=page_size, resource_type=resource_type, resource_id=resource_id)

    def list_by_correlation(self, db: Session, correlation_id: str, *, page: int = 1, page_size: int = 20) -> tuple[builtins.list[LogisticsAuditEvent], int]:
        return self.list(db, page=page, page_size=page_size, correlation_id=correlation_id)

    def verify_integrity(self, db: Session, event_id: UUID) -> dict:
        event = self.get_by_id(db, event_id)
        if not event:
            raise ApplicationError("AUDIT_EVENT_NOT_FOUND", "El evento de auditoría no existe.", 404)
        computed = _compute_hash(event)
        return {
            "success": True,
            "event_id": event.id,
            "valid": event.event_hash == computed,
            "stored_hash": event.event_hash,
            "computed_hash": computed,
        }


audit_service = AuditService()
