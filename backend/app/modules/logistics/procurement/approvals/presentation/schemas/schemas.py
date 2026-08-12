"""Pydantic v2 schemas for Phase 035 — Procurement Approvals Engine API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Policy & Version Schemas
# ---------------------------------------------------------------------------
class PolicyCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    subject_type: str = Field(..., max_length=50)  # PURCHASE_ORDER, REVISION, AMENDMENT, etc.
    description: str | None = None
    priority: int = Field(default=100, ge=1, le=9999)
    effective_scope: str = Field(default="ORGANIZATION", max_length=50)
    is_fallback: bool = False


class PolicyResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    normalized_code: str
    name: str
    description: str | None
    subject_type: str
    priority: int
    status: str
    active_version_id: UUID | None
    effective_scope: str
    is_fallback: bool
    created_at: datetime
    updated_at: datetime


class PolicyConditionCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_group: str = Field(default="ALL", max_length=20)
    field_code: str = Field(..., max_length=50)
    operator: str = Field(..., max_length=30)
    value_data: dict[str, Any]
    order_index: int = Field(default=1, ge=1)


class StepDefinitionCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    order_index: int = Field(default=1, ge=1)
    execution_mode: str = Field(default="SEQUENTIAL", max_length=20)
    completion_mode: str = Field(default="ALL", max_length=30)
    minimum_approvals: int = Field(default=1, ge=1)
    required_approvals: int = Field(default=1, ge=1)
    approver_source_type: str = Field(..., max_length=50)
    approver_source_config: dict[str, Any]
    step_up_level: str = Field(default="HIGH", max_length=20)
    distinct_from_creator: bool = True


# ---------------------------------------------------------------------------
# Request & Decision Schemas
# ---------------------------------------------------------------------------
class ApprovalSubmitSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    subject_type: str = Field(..., max_length=50)
    subject_id: UUID
    subject_revision_id: UUID | None = None
    subject_code: str | None = None
    subject_snapshot: dict[str, Any]
    amount: str = Field(..., description="Decimal monetary amount string")
    currency_code: str = Field(..., min_length=3, max_length=3)
    creator_user_id: UUID
    requester_user_id: UUID
    cost_center_snapshot: dict[str, Any] | None = None
    category_snapshots: list[dict[str, Any]] | None = None
    branch_snapshot: dict[str, Any] | None = None


class DecisionRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_type: str = Field(..., max_length=30)  # APPROVE, REJECT, RETURN_FOR_CHANGES, ABSTAIN
    reason: str | None = None
    conditions: dict[str, Any] | None = None
    step_up_assurance_level: str = Field(default="HIGH", max_length=20)


class ApprovalRequestResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    request_code: str
    subject_type: str
    subject_id: UUID
    subject_revision_id: UUID | None
    subject_code: str | None
    status: str
    current_sequence: int
    amount: str
    currency_code: str
    submitted_at: datetime
    completed_at: datetime | None
    final_decision: str | None
    audit_seal_id: UUID | None


class AuditSealVerificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    valid: bool
    verification_status: str
    seal_hash: str
    verified_at: datetime
    mismatches: list[str] = []
