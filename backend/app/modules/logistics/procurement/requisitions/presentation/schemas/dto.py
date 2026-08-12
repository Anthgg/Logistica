"""Pydantic v2 schemas/DTOs for Purchase Requisitions (Phase 031)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# -------------------------------------------------------------------------
# Cost Center DTOs
# -------------------------------------------------------------------------


class CostCenterCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    branch_id: UUID | None = None
    responsible_user_id: UUID | None = None
    parent_cost_center_id: UUID | None = None
    valid_from: date = Field(default_factory=date.today)
    valid_until: date | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper().replace(" ", "_")


class CostCenterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    responsible_user_id: UUID | None = None
    valid_until: date | None = None
    row_version: int = Field(..., ge=1)


class CostCenterResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID | None
    code: str
    normalized_code: str
    name: str
    description: str | None
    responsible_user_id: UUID | None
    parent_cost_center_id: UUID | None
    status: str
    valid_from: date
    valid_until: date | None
    created_by: UUID
    updated_by: UUID
    row_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CostCenterSummary(BaseModel):
    id: UUID
    code: str
    name: str
    status: str
    organization_id: UUID
    branch_id: UUID | None

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Requisition DTOs
# -------------------------------------------------------------------------


class RequisitionCreateRequest(BaseModel):
    branch_id: UUID
    cost_center_id: UUID
    priority: str = Field(default="NORMAL", pattern=r"^(LOW|NORMAL|HIGH|URGENT|CRITICAL)$")
    required_date: date
    justification: str = Field(..., min_length=20, max_length=2000)
    requester_area: str | None = Field(default=None, max_length=150)
    business_purpose: str | None = Field(default=None, max_length=2000)
    destination_warehouse_id: UUID | None = None
    delivery_location_description: str | None = Field(default=None, max_length=500)


class RequisitionUpdateRequest(BaseModel):
    priority: str | None = Field(default=None, pattern=r"^(LOW|NORMAL|HIGH|URGENT|CRITICAL)$")
    required_date: date | None = None
    justification: str | None = Field(default=None, min_length=20, max_length=2000)
    requester_area: str | None = None
    business_purpose: str | None = None
    destination_warehouse_id: UUID | None = None
    delivery_location_description: str | None = None
    row_version: int = Field(..., ge=1)


class RequisitionSubmitRequest(BaseModel):
    row_version: int = Field(..., ge=1)
    idempotency_key: str | None = None
    override_duplicate_warning: bool = False
    duplicate_justification: str | None = None


class RequisitionApproveRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class RequisitionRejectRequest(BaseModel):
    reason: str = Field(..., min_length=15, max_length=2000)


class RequisitionReturnRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=2000)


class RequisitionWithdrawRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=2000)


class RequisitionCancelRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=2000)


# -------------------------------------------------------------------------
# Line DTOs
# -------------------------------------------------------------------------


class LineCreateRequest(BaseModel):
    product_id: UUID
    requested_quantity: str = Field(
        ...,
        description="Decimal quantity as string — e.g. '12.5'. Never use float.",
        min_length=1,
    )
    requested_unit_id: UUID
    line_justification: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)
    manufacturer_reference: str | None = Field(default=None, max_length=200)
    preferred_brand_reference: str | None = Field(default=None, max_length=200)
    required_date: date | None = None
    destination_warehouse_id: UUID | None = None
    specifications: dict | None = None
    priority_override: str | None = Field(
        default=None, pattern=r"^(LOW|NORMAL|HIGH|URGENT|CRITICAL)$"
    )


class LineUpdateRequest(BaseModel):
    requested_quantity: str | None = Field(default=None, min_length=1)
    requested_unit_id: UUID | None = None
    line_justification: str | None = None
    notes: str | None = None
    manufacturer_reference: str | None = None
    preferred_brand_reference: str | None = None
    required_date: date | None = None
    destination_warehouse_id: UUID | None = None
    specifications: dict | None = None
    priority_override: str | None = None


class LineReorderRequest(BaseModel):
    line_ids: list[UUID] = Field(..., min_length=1)


class LineResponse(BaseModel):
    id: UUID
    revision_id: UUID
    line_number: int
    product_id: UUID
    product_version_id: UUID | None
    sku_snapshot: str
    product_name_snapshot: str
    requested_quantity: Decimal
    requested_unit_id: UUID
    base_quantity: Decimal
    base_unit_id: UUID
    conversion_rule_id: UUID | None
    conversion_factor_snapshot: Decimal | None
    required_date: date | None
    line_justification: str | None
    notes: str | None
    manufacturer_reference: str | None
    preferred_brand_reference: str | None
    status: str
    row_version: int
    created_at: datetime

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Revision DTOs
# -------------------------------------------------------------------------


class RevisionSummary(BaseModel):
    id: UUID
    revision_number: int
    status: str
    line_count: int
    content_hash: str | None
    created_by: UUID
    created_at: datetime
    submitted_at: datetime | None
    frozen_at: datetime | None

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Comment DTOs
# -------------------------------------------------------------------------


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=3, max_length=2000)
    comment_type: str = Field(
        default="GENERAL",
        pattern=r"^(GENERAL|REQUESTER_NOTE|REVIEWER_NOTE|SYSTEM_NOTE)$",
    )
    visibility: str = Field(
        default="INTERNAL",
        pattern=r"^(INTERNAL|REQUESTER_AND_REVIEWERS)$",
    )


class CommentResponse(BaseModel):
    id: UUID
    requisition_id: UUID
    comment_type: str
    body: str
    visibility: str
    created_by: UUID
    created_at: datetime
    status: str

    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Full Requisition Response
# -------------------------------------------------------------------------


class RequisitionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    requisition_code: str | None
    document_instance_id: UUID | None
    requester_user_id: UUID
    requester_name_snapshot: str
    requester_area: str | None
    cost_center_id: UUID
    cost_center_snapshot: dict | None
    priority: str
    required_date: date
    destination_warehouse_id: UUID | None
    delivery_location_description: str | None
    justification: str
    business_purpose: str | None
    status: str
    current_revision_number: int
    active_revision_id: UUID | None
    submitted_at: datetime | None
    submitted_by: UUID | None
    approved_at: datetime | None
    approved_by: UUID | None
    rejected_at: datetime | None
    rejected_by: UUID | None
    created_by: UUID
    updated_by: UUID
    row_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequisitionListResponse(BaseModel):
    items: list[RequisitionResponse]
    total: int
    skip: int
    limit: int


class CapabilitiesResponse(BaseModel):
    can_edit: bool
    can_submit: bool
    can_start_review: bool
    can_approve: bool
    can_reject: bool
    can_return: bool
    can_withdraw: bool
    can_cancel: bool
    can_preview: bool
    can_issue_document: bool
    can_copy: bool
    current_status: str
    current_revision_number: int


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    blocking_issues: list[str]
    line_results: list[dict]
    line_count: int


class HistoryEntry(BaseModel):
    event: str
    actor: str
    timestamp: str | None
    details: dict


class HistoryResponse(BaseModel):
    requisition_id: UUID
    history: list[HistoryEntry]
