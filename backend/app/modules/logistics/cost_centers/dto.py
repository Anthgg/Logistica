"""Pydantic v2 schemas/DTOs for Cost Centers (Phase 031)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
