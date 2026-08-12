"""Phase 041. Quality inspection plan presentation schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_float(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("Use una cadena decimal; float no está permitido")
        return value


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


JsonObject = dict[str, Any]


class QualityPlanCreate(CommandModel):
    plan_code: str = Field(max_length=80)
    plan_name: str = Field(max_length=300)
    description: str | None = None
    plan_family: str = Field(default="GENERAL_QUALITY", max_length=40)
    is_global: bool = False
    priority: int = 0
    metadata_json: JsonObject | None = None


class QualityPlanUpdate(CommandModel):
    plan_name: str | None = Field(default=None, max_length=300)
    description: str | None = None
    plan_family: str | None = Field(default=None, max_length=40)
    is_global: bool | None = None
    priority: int | None = None
    metadata_json: JsonObject | None = None


class QualityPlanResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    plan_code: str
    plan_name: str
    description: str | None
    plan_family: str
    status: str
    current_version_number: int
    active_version_id: UUID | None
    is_global: bool
    priority: int
    metadata_json: JsonObject | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int


class QualityPlanSummary(ORMResponse):
    id: UUID
    plan_code: str
    plan_name: str
    plan_family: str
    status: str
    current_version_number: int
    is_global: bool
    created_at: datetime


class QualityPlanVersionCreate(CommandModel):
    change_summary: str | None = None
    plan_snapshot: JsonObject | None = None


class QualityPlanVersionResponse(ORMResponse):
    id: UUID
    plan_id: UUID
    version_number: int
    status: str
    change_summary: str | None
    plan_snapshot: JsonObject | None
    content_hash: str | None
    validation_errors: JsonObject | None
    activated_at: datetime | None
    activated_by: UUID | None
    retired_at: datetime | None
    retired_by: UUID | None
    scheduled_activation_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int


class QualityPlanScopeCreate(CommandModel):
    scope_type: str = Field(max_length=30)
    scope_product_id: UUID | None = None
    scope_product_name: str | None = Field(default=None, max_length=300)
    scope_category_id: UUID | None = None
    scope_category_name: str | None = Field(default=None, max_length=200)
    scope_warehouse_id: UUID | None = None
    scope_warehouse_name: str | None = Field(default=None, max_length=200)
    scope_branch_id: UUID | None = None
    scope_branch_name: str | None = Field(default=None, max_length=200)
    resolution_specificity: str | None = Field(default=None, max_length=40)
    is_active: bool = True


class QualityPlanScopeResponse(ORMResponse):
    id: UUID
    plan_id: UUID
    version_id: UUID | None
    scope_type: str
    scope_product_id: UUID | None
    scope_product_name: str | None
    scope_category_id: UUID | None
    scope_category_name: str | None
    scope_warehouse_id: UUID | None
    scope_warehouse_name: str | None
    scope_branch_id: UUID | None
    scope_branch_name: str | None
    resolution_specificity: str | None
    is_active: bool
    created_at: datetime


class QualityControlCreate(CommandModel):
    scope_id: UUID | None = None
    control_type: str = Field(max_length=60)
    control_code: str = Field(max_length=80)
    control_name: str = Field(max_length=300)
    description: str | None = None
    display_order: int = 0
    is_mandatory: bool = True
    is_blocking: bool = False
    applies_to_all_units: bool = False
    applies_to_sample: bool = True
    configuration_json: JsonObject | None = None


class QualityControlUpdate(CommandModel):
    control_name: str | None = Field(default=None, max_length=300)
    description: str | None = None
    display_order: int | None = None
    is_mandatory: bool | None = None
    is_blocking: bool | None = None
    applies_to_all_units: bool | None = None
    applies_to_sample: bool | None = None
    configuration_json: JsonObject | None = None


class QualityControlResponse(ORMResponse):
    id: UUID
    plan_id: UUID
    version_id: UUID | None
    scope_id: UUID | None
    control_type: str
    control_code: str
    control_name: str
    description: str | None
    display_order: int
    is_mandatory: bool
    is_blocking: bool
    applies_to_all_units: bool
    applies_to_sample: bool
    configuration_json: JsonObject | None
    created_at: datetime
    updated_at: datetime


class QualityToleranceCreate(CommandModel):
    tolerance_type: str = Field(max_length=40)
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    target_value: Decimal | None = None
    absolute_deviation: Decimal | None = None
    percentage_deviation: Decimal | None = None
    valid_options: JsonObject | None = None
    default_value: JsonObject | None = None
    unit_code: str | None = Field(default=None, max_length=20)
    description: str | None = None


class QualityToleranceResponse(ORMResponse):
    id: UUID
    control_id: UUID
    tolerance_type: str
    min_value: Decimal | None
    max_value: Decimal | None
    target_value: Decimal | None
    absolute_deviation: Decimal | None
    percentage_deviation: Decimal | None
    valid_options: JsonObject | None
    default_value: JsonObject | None
    unit_code: str | None
    description: str | None
    created_at: datetime


class QualitySamplingCreate(CommandModel):
    sampling_type: str = Field(max_length=40)
    fixed_count: int | None = None
    percentage: Decimal | None = None
    minimum_count: int | None = None
    package_level: str | None = Field(default=None, max_length=40)
    lot_level: str | None = Field(default=None, max_length=40)
    custom_formula: str | None = None
    description: str | None = None


class QualitySamplingResponse(ORMResponse):
    id: UUID
    control_id: UUID
    sampling_type: str
    fixed_count: int | None
    percentage: Decimal | None
    minimum_count: int | None
    package_level: str | None
    lot_level: str | None
    custom_formula: str | None
    description: str | None
    created_at: datetime


class QualityCertificateCreate(CommandModel):
    certificate_type: str = Field(max_length=60)
    document_type_id: UUID | None = None
    is_mandatory: bool = True
    validity_days: int | None = None
    requires_signature: bool = False
    metadata_schema: JsonObject | None = None
    description: str | None = None


class QualityCertificateResponse(ORMResponse):
    id: UUID
    control_id: UUID
    certificate_type: str
    document_type_id: UUID | None
    is_mandatory: bool
    validity_days: int | None
    requires_signature: bool
    metadata_schema: JsonObject | None
    description: str | None
    created_at: datetime


class QualityConditionCreate(CommandModel):
    condition_type: str = Field(max_length=40)
    condition_field: str = Field(max_length=120)
    condition_operator: str = Field(max_length=20)
    condition_value: JsonObject
    description: str | None = None


class QualityConditionResponse(ORMResponse):
    id: UUID
    control_id: UUID
    condition_type: str
    condition_field: str
    condition_operator: str
    condition_value: JsonObject
    description: str | None
    created_at: datetime


class QualityPlanReferenceFileCreate(CommandModel):
    file_asset_id: UUID
    file_version_id: UUID | None = None
    reference_type: str = Field(default="MANUAL", max_length=40)
    description: str | None = None


class QualityPlanReferenceFileResponse(ORMResponse):
    id: UUID
    plan_id: UUID
    version_id: UUID | None
    file_asset_id: UUID
    file_version_id: UUID | None
    reference_type: str
    description: str | None
    linked_by: UUID
    linked_at: datetime
    content_hash: str | None


class QualityPlanConflictResponse(BaseModel):
    plan_id: str
    plan_code: str
    scope_id: str
    scope_type: str
    conflict_type: str


class QualityPlanResolutionResponse(BaseModel):
    resolved_plan_id: str | None
    resolution_specificity: str
    candidate_plans_count: int


class QualityPlanValidationResponse(BaseModel):
    plan_id: str
    is_valid: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    controls_count: int
    scopes_count: int


class QualityPlanIntegrityResponse(BaseModel):
    plan_id: str
    plan_code: str
    status: str
    stored_hash: str | None
    computed_hash: str | None
    verified_at: str


class QualityPlanMetricsResponse(BaseModel):
    plan_id: str
    total_scopes: int
    total_controls: int
    mandatory_controls: int
    blocking_controls: int
    total_tolerances: int
    total_sampling_plans: int
    total_certificate_requirements: int
    total_reference_files: int
    resolved_for_products: int
    resolved_for_categories: int
    calculated_at: str | None


class QualityPlanSnapshotResponse(BaseModel):
    canonicalization_version: str
    plan: JsonObject
    scopes: list[JsonObject]
    controls: list[JsonObject]
    reference_files: list[JsonObject]
    content_hash: str
    captured_at: str


class QualityPlanUsageProjectionResponse(BaseModel):
    plan_id: str
    total_scopes: int
    total_controls: int
    mandatory_controls: int
    blocking_controls: int
    total_tolerances: int
    total_sampling_plans: int
    total_certificate_requirements: int
    total_reference_files: int
    resolved_for_products: int
    resolved_for_categories: int


class QualityPlanFutureTemplateCreate(CommandModel):
    product_id: UUID | None = None
    product_category_id: UUID | None = None
    warehouse_id: UUID | None = None
    branch_id: UUID | None = None


class QualityPlanFutureTemplateResponse(BaseModel):
    resolved_plan_id: str | None
    resolution_specificity: str
    plan_code: str | None
    plan_name: str | None
    is_applicable: bool
    control_count: int
