"""Audit schemas for Phase 007."""

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AuditEventSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    event_code: str
    event_category: str
    actor_user_id: UUID | None = None
    actor_display_name_snapshot: str | None = None
    action: str | None = None
    result: str
    severity: str
    resource_type: str | None = None
    resource_id: str | None = None
    resource_code: str | None = None
    organization_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    occurred_at: datetime


class AuditEventDetailResponse(AuditEventSummaryResponse):
    event_version: str = "1.0"
    actor_type: str = "user"
    actor_role_codes_snapshot: str | None = None
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
    parent_resource_type: str | None = None
    parent_resource_id: str | None = None
    reason_code: str | None = None
    reason_text: str | None = None
    previous_data: dict | None = None
    new_data: dict | None = None
    changed_fields: list[str] | None = None
    metadata_: dict | None = Field(default=None, serialization_alias="metadata", validation_alias=AliasChoices("metadata_", "metadata"))
    source_module: str | None = None
    source_service: str | None = None
    event_hash: str | None = None
    hash_algorithm: str = "sha256"
    schema_version: str = "1.0"


class IntegrityCheckResponse(BaseModel):
    success: bool = True
    event_id: UUID
    valid: bool
    stored_hash: str | None = None
    computed_hash: str | None = None