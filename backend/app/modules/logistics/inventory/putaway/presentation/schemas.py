"""Phase 043 — Putaway Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PutawayBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Policy
# =============================================================================
class PolicyCreateRequest(PutawayBaseSchema):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=150)
    description: str | None = None


class PolicyVersionCreateRequest(PutawayBaseSchema):
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    warehouse_id: UUID | None = None
    branch_id: UUID | None = None
    product_category_id: UUID | None = None
    product_id: UUID | None = None
    priority: int = Field(default=0, ge=0)
    capacity_weight: Decimal = Field(default=Decimal("0.25"), ge=0, le=1)
    rotation_weight: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    picking_proximity_weight: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    consolidation_weight: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    fragmentation_penalty_weight: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    travel_cost_weight: Decimal = Field(default=Decimal("0.15"), ge=0, le=1)
    manual_override_allowed: bool = True
    partial_putaway_allowed: bool = True
    split_destination_allowed: bool = True
    reservation_expiration_minutes: int = Field(default=30, ge=1)
    maximum_candidate_count: int = Field(default=50, ge=1)
    minimum_score: Decimal | None = None


class PolicyResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    code: str
    name: str
    description: str | None
    status: str
    active_version_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int


class PolicyVersionResponse(PutawayBaseSchema):
    id: UUID
    policy_id: UUID
    version_number: int
    status: str
    effective_from: datetime
    effective_to: datetime | None
    warehouse_id: UUID | None
    branch_id: UUID | None
    product_category_id: UUID | None
    product_id: UUID | None
    priority: int
    capacity_weight: Decimal
    rotation_weight: Decimal
    picking_proximity_weight: Decimal
    consolidation_weight: Decimal
    fragmentation_penalty_weight: Decimal
    travel_cost_weight: Decimal
    manual_override_allowed: bool
    partial_putaway_allowed: bool
    split_destination_allowed: bool
    reservation_expiration_minutes: int
    maximum_candidate_count: int
    minimum_score: Decimal | None
    created_by: UUID
    created_at: datetime
    activated_at: datetime | None


class PolicyListResponse(PutawayBaseSchema):
    items: list[PolicyResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Compatibility Rules
# =============================================================================
class CompatibilityRuleCreateRequest(PutawayBaseSchema):
    warehouse_id: UUID
    location_id: UUID | None = None
    location_type: str | None = None
    product_id: UUID | None = None
    product_category_id: UUID | None = None
    rule_type: str
    action: str = "ALLOW"
    required_value: dict | None = None
    severity: str = "MEDIUM"
    reason: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class CompatibilityRuleResponse(PutawayBaseSchema):
    id: UUID
    policy_version_id: UUID | None
    warehouse_id: UUID
    location_id: UUID | None
    location_type: str | None
    product_id: UUID | None
    product_category_id: UUID | None
    rule_type: str
    action: str
    required_value: dict | None
    severity: str
    reason: str | None
    effective_from: datetime
    effective_to: datetime | None
    status: str
    created_at: datetime


class CompatibilityEvaluationResponse(PutawayBaseSchema):
    compatible: bool
    action: str
    severity: str
    matched_rules: list[dict[str, Any]]
    warnings: list[str]


# =============================================================================
# Capacity
# =============================================================================
class CapacityProfileCreateRequest(PutawayBaseSchema):
    warehouse_location_id: UUID
    capacity_type: str
    maximum_value: Decimal = Field(gt=0)
    unit_id: UUID
    safety_margin_value: Decimal = Field(default=Decimal("0"), ge=0)
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class CapacityProfileResponse(PutawayBaseSchema):
    id: UUID
    warehouse_location_id: UUID
    capacity_type: str
    maximum_value: Decimal
    unit_id: UUID
    safety_margin_value: Decimal
    reservation_limit_value: Decimal | None
    effective_from: datetime
    effective_to: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime


class CapacityEvaluationResponse(PutawayBaseSchema):
    location_id: UUID
    capacity_profile_id: UUID
    capacity_type: str
    maximum_value: Decimal
    safety_margin_value: Decimal
    operational_occupied: Decimal
    active_reserved: Decimal
    projected_free: Decimal
    has_enough: bool
    data_quality_status: str
    unit_id: UUID


class CapacityProjectionResponse(PutawayBaseSchema):
    organization_id: UUID
    warehouse_id: UUID
    location_id: UUID
    capacity_profile_id: UUID
    capacity_type: str
    maximum_value: Decimal
    safety_margin_value: Decimal
    operational_occupied_value: Decimal
    active_reserved_value: Decimal
    projected_free_value: Decimal
    unit_id: UUID
    data_quality_status: str
    last_placement_at: datetime | None
    calculated_at: datetime
    projection_version: int


# =============================================================================
# Proximity
# =============================================================================
class ProximityProfileCreateRequest(PutawayBaseSchema):
    warehouse_id: UUID
    source_location_id: UUID
    target_zone_id: UUID | None = None
    target_location_id: UUID | None = None
    metric_type: str
    metric_value: Decimal
    metric_unit: str
    source_type: str = "MANUAL_MEASUREMENT"
    measured_at: datetime | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class ProximityProfileResponse(PutawayBaseSchema):
    id: UUID
    warehouse_id: UUID
    source_location_id: UUID
    target_zone_id: UUID | None
    target_location_id: UUID | None
    metric_type: str
    metric_value: Decimal
    metric_unit: str
    source_type: str
    measured_at: datetime | None
    effective_from: datetime
    effective_to: datetime | None
    status: str
    created_at: datetime


class ProximityResultResponse(PutawayBaseSchema):
    source_location_id: UUID
    target_location_id: UUID | None
    target_zone_id: UUID | None
    metric_type: str
    metric_value: Decimal
    metric_unit: str
    source_type: str


class TravelCostScoreResponse(PutawayBaseSchema):
    walking_distance: Decimal | None
    travel_time: Decimal | None
    normalized_distance: Decimal
    score: Decimal


# =============================================================================
# Recommendations
# =============================================================================
class RecommendationRequest(PutawayBaseSchema):
    source_allocation_id: UUID
    requested_quantity: Decimal = Field(gt=0)
    requested_unit_id: UUID
    source_location_id: UUID


class CandidateResponse(PutawayBaseSchema):
    id: UUID
    location_id: UUID
    rank: int
    compatible: bool
    capacity_available: bool
    capacity_score: Decimal
    rotation_score: Decimal
    picking_proximity_score: Decimal
    consolidation_score: Decimal
    fragmentation_score: Decimal
    travel_cost_score: Decimal
    penalty_score: Decimal
    total_score: Decimal
    capacity_snapshot: dict | None
    compatibility_snapshot: dict | None
    proximity_snapshot: dict | None
    rotation_snapshot: dict | None
    explanation: dict | None
    status: str
    created_at: datetime


class RecommendationRunResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    source_allocation_id: UUID
    policy_version_id: UUID
    status: str
    requested_quantity: Decimal
    requested_unit_id: UUID
    requested_base_quantity: Decimal
    candidate_count: int
    eligible_candidate_count: int
    scoring_version: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_by: UUID
    created_at: datetime
    candidates: list[CandidateResponse] = []


# =============================================================================
# Orders
# =============================================================================
class OrderCreateRequest(PutawayBaseSchema):
    warehouse_id: UUID
    source_type: str = "QUALITY_RELEASE"
    priority: int = Field(default=0, ge=0)


class OrderIssueRequest(PutawayBaseSchema):
    pass


class OrderCancelRequest(PutawayBaseSchema):
    reason: str = Field(..., min_length=1, max_length=500)


class OrderResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    order_code: str
    status: str
    source_type: str
    priority: int
    task_count: int
    completed_task_count: int
    exception_task_count: int
    issued_at: datetime | None
    issued_by: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    current_revision_number: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int


class OrderListResponse(PutawayBaseSchema):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderRevisionResponse(PutawayBaseSchema):
    id: UUID
    putaway_order_id: UUID
    revision_number: int
    status: str
    change_reason: str | None
    created_by: UUID
    created_at: datetime
    frozen_at: datetime | None


# =============================================================================
# Tasks
# =============================================================================
class TaskCreateRequest(PutawayBaseSchema):
    putaway_order_id: UUID
    source_allocation_id: UUID
    required_quantity: Decimal = Field(gt=0)
    required_unit_id: UUID
    expected_product_id: UUID
    priority: int = Field(default=0, ge=0)
    scan_policy: str = "PRODUCT_THEN_LOCATION"


class TaskAssignRequest(PutawayBaseSchema):
    user_id: UUID


class TaskResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    putaway_order_id: UUID
    task_number: str
    source_allocation_id: UUID
    recommendation_run_id: UUID | None
    recommended_location_id: UUID | None
    selected_location_id: UUID | None
    source_stage_location_id: UUID | None
    status: str
    priority: int
    assignment_status: str
    assigned_user_id: UUID | None
    assigned_team_id: UUID | None
    assigned_at: datetime | None
    required_quantity: Decimal
    required_unit_id: UUID
    required_base_quantity: Decimal
    placed_quantity: Decimal
    placed_base_quantity: Decimal
    remaining_quantity: Decimal
    remaining_base_quantity: Decimal
    scan_policy: str
    expected_product_id: UUID
    started_at: datetime | None
    paused_at: datetime | None
    completed_at: datetime | None
    exception_count: int
    created_at: datetime
    updated_at: datetime
    row_version: int


class TaskListResponse(PutawayBaseSchema):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskDestinationResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    location_id: UUID
    sequence_number: int
    recommended_quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    reservation_id: UUID | None
    status: str
    created_at: datetime


class TaskAssignmentResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    assignment_type: str
    user_id: UUID | None
    team_id: UUID | None
    status: str
    assigned_by: UUID
    assigned_at: datetime
    accepted_at: datetime | None
    declined_at: datetime | None
    decline_reason: str | None
    completed_at: datetime | None
    created_at: datetime


# =============================================================================
# Reservations
# =============================================================================
class ReservationCreateRequest(PutawayBaseSchema):
    location_id: UUID
    task_id: UUID
    source_allocation_id: UUID
    capacity_profile_id: UUID
    reserved_value: Decimal = Field(gt=0)
    unit_id: UUID
    expires_in_minutes: int = Field(default=30, ge=1)


class ReservationResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    location_id: UUID
    task_id: UUID
    source_allocation_id: UUID
    capacity_profile_id: UUID
    reserved_value: Decimal
    unit_id: UUID
    reserved_base_quantity: Decimal
    status: str
    reserved_at: datetime
    expires_at: datetime
    released_at: datetime | None
    consumed_at: datetime | None
    cancellation_reason: str | None
    row_version: int
    created_at: datetime


# =============================================================================
# Execution Sessions
# =============================================================================
class ExecutionSessionCreateRequest(PutawayBaseSchema):
    scanner_type: str = "HANDHELD_TERMINAL"
    device_reference_hash: str | None = None
    client_session_reference: str | None = None


class ExecutionSessionResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    operator_user_id: UUID
    device_reference_hash: str | None
    scanner_type: str
    status: str
    started_at: datetime
    last_activity_at: datetime
    paused_at: datetime | None
    completed_at: datetime | None
    client_session_reference: str | None
    created_at: datetime


# =============================================================================
# Scans
# =============================================================================
class ScanRecordRequest(PutawayBaseSchema):
    client_scan_id: str = Field(..., max_length=200)
    scan_type: str
    normalized_code: str = Field(..., max_length=200)
    code_hash: str = Field(..., max_length=64)
    symbology: str | None = None
    raw_code_encrypted: str | None = None


class ScanEventResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    task_id: UUID
    execution_session_id: UUID
    client_scan_id: str
    server_sequence: int
    scan_type: str
    normalized_code: str
    code_hash: str
    symbology: str | None
    resolution_status: str
    resolved_product_id: UUID | None
    resolved_location_id: UUID | None
    validation_status: str | None
    received_at: datetime
    operator_user_id: UUID
    status: str
    created_at: datetime


class ScanValidationRequest(PutawayBaseSchema):
    expected_product_id: UUID | None = None
    expected_location_id: UUID | None = None


# =============================================================================
# Placements
# =============================================================================
class PlacementConfirmRequest(PutawayBaseSchema):
    source_allocation_id: UUID
    location_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_id: UUID
    product_scan_event_id: UUID | None = None
    location_scan_event_id: UUID | None = None
    reservation_id: UUID | None = None
    observation: str | None = None


class PlacementConfirmationResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    task_id: UUID
    source_allocation_id: UUID
    location_id: UUID
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    product_scan_event_id: UUID | None
    location_scan_event_id: UUID | None
    reservation_id: UUID | None
    confirmation_status: str
    confirmed_by: UUID
    confirmed_at: datetime
    observation: str | None
    content_hash: str | None
    created_at: datetime


class OperationalPlacementResponse(PutawayBaseSchema):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    location_id: UUID
    source_allocation_id: UUID
    putaway_order_id: UUID
    putaway_task_id: UUID
    placement_confirmation_id: UUID
    product_id: UUID
    product_version_id: UUID | None
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    quality_release_hash: str | None
    status: str
    placed_at: datetime
    placed_by: UUID
    content_hash: str | None
    created_at: datetime


# =============================================================================
# Overrides
# =============================================================================
class OverrideRequest(PutawayBaseSchema):
    recommended_location_id: UUID
    selected_location_id: UUID
    recommendation_run_id: UUID
    recommended_score: Decimal
    selected_score: Decimal
    reason_code: str
    reason: str = Field(..., min_length=1, max_length=500)


class OverrideApprovalRequest(PutawayBaseSchema):
    approved_by: UUID
    step_up_summary: dict | None = None


class OverrideResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    recommended_location_id: UUID
    selected_location_id: UUID
    recommendation_run_id: UUID
    recommended_score: Decimal
    selected_score: Decimal
    reason_code: str
    reason: str
    requested_by: UUID
    approved_by: UUID | None
    step_up_assurance_summary: dict | None
    created_at: datetime


# =============================================================================
# Exceptions
# =============================================================================
class ExceptionReportRequest(PutawayBaseSchema):
    exception_type: str
    severity: str = "MEDIUM"
    description: str = Field(..., min_length=1, max_length=1000)
    product_scan_event_id: UUID | None = None
    location_scan_event_id: UUID | None = None
    location_id: UUID | None = None
    quantity: Decimal | None = None
    unit_id: UUID | None = None
    evidence_file_ids: list[str] | None = None


class ExceptionResolveRequest(PutawayBaseSchema):
    resolution: str = Field(..., min_length=1, max_length=500)


class ExceptionResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    exception_type: str
    severity: str
    product_scan_event_id: UUID | None
    location_scan_event_id: UUID | None
    location_id: UUID | None
    quantity: Decimal | None
    unit_id: UUID | None
    description: str
    evidence_file_ids: list[str] | None
    status: str
    detected_by: UUID
    detected_at: datetime
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution: str | None
    created_at: datetime


# =============================================================================
# Pauses
# =============================================================================
class PauseRequest(PutawayBaseSchema):
    reason: str
    description: str | None = None


class PauseResponse(PutawayBaseSchema):
    id: UUID
    task_id: UUID
    pause_reason: str
    description: str | None
    paused_by: UUID
    paused_at: datetime
    resumed_at: datetime | None
    created_at: datetime


# =============================================================================
# Placement Projections
# =============================================================================
class PlacementProjectionResponse(PutawayBaseSchema):
    organization_id: UUID
    warehouse_id: UUID
    location_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    placement_count: int
    active_reservation_value: Decimal
    operational_capacity_used: Decimal
    operational_capacity_free: Decimal
    data_quality_status: str
    last_putaway_at: datetime | None
    calculated_at: datetime
    projection_version: int
