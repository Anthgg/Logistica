"""Audit schemas for Phase 007."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEventSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_code: str
    event_category: str
    actor_user_id: UUID | None
    actor_display_name_snapshot: str | None
    action: str | None
    result: str
    severity: str
    resource_type: str | None
    resource_id: str | None
    organization_id: UUID | None
    branch_id: UUID | None
    warehouse_id: UUID | None
    occurred_at: datetime


class AuditEventDetailResponse(AuditEventSummaryResponse):
    event_version: str
    actor_type: str
    actor_role_codes_snapshot: str | None
    session_id: UUID | None
    device_id: UUID | None
    authentication_level: str | None
    risk_score: float | None
    step_up_required: bool
    step_up_result: str | None
    request_id: str | None
    correlation_id: str | None
    method: str | None
    endpoint: str | None
    ip_address: str | None
    user_agent: str | None
    origin: str | None
    resource_code: str | None
    parent_resource_type: str | None
    parent_resource_id: str | None
    reason_code: str | None
    reason_text: str | None
    previous_data: dict | None
    new_data: dict | None
    changed_fields: list[str] | None
    metadata_: dict | None = None
    source_module: str | None
    source_service: str | None
    event_hash: str | None
    schema_version: str


class IntegrityCheckResponse(BaseModel):
    success: bool = True
    event_id: UUID
    valid: bool
    stored_hash: str | None
    computed_hash: str | None