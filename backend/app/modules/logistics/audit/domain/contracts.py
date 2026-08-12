"""Audit domain — contracts for logistics audit events.

Reuses the existing ``AuditService`` via an adapter rather than creating
a parallel audit table.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    ISSUE = "issue"
    CANCEL = "cancel"
    REPRINT = "reprint"
    APPROVE = "approve"
    REJECT = "reject"


class AuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class AuditEvent:
    """A logistics audit event."""
    user_id: UUID
    session_id: UUID | None
    device_id: UUID | None
    ip_address: str | None
    module: str
    resource_type: str
    resource_id: UUID
    action: AuditAction
    result: AuditResult
    timestamp: datetime
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    reason: str | None = None
    correlation_id: str | None = None
    risk_level: str | None = None
    step_up_result: str | None = None


class AuditEventWriter(Protocol):
    """Writes audit events to the audit log."""

    async def write(self, event: AuditEvent) -> None: ...


class AuditEventReader(Protocol):
    """Reads audit events for a resource or user."""

    async def list_for_resource(self, resource_type: str, resource_id: UUID) -> list[AuditEvent]: ...

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[AuditEvent]: ...


class AuditContextProvider(Protocol):
    """Provides context for the current audit event (IP, session, etc.)."""

    def current_context(self) -> dict[str, str | None]: ...


class AuditSerializer(Protocol):
    """Serializes audit events for storage or transport."""

    def serialize(self, event: AuditEvent) -> dict[str, object]: ...