"""Pydantic v2 contracts for Phase 038.

Command payloads reject unknown fields so client-supplied authoritative users,
timestamps, states, or durations cannot be silently accepted.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.modules.logistics.inbound.dock_operations.domain.enums import (
    AssignmentMode,
    CheckResult,
    DockOperationDirection,
    DockResourceType,
    QueuePriority,
    ResponsibilityType,
    UnloadingMethod,
)

JsonObject = dict[str, JsonValue]
PositiveDecimal = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WarehouseDockCreate(CommandModel):
    warehouse_id: UUID
    branch_id: UUID
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    resource_type: DockResourceType = DockResourceType.DOCK
    operation_direction: DockOperationDirection = DockOperationDirection.INBOUND
    physical_zone: str | None = Field(default=None, max_length=120)
    warehouse_location_id: UUID | None = None
    timezone: str = Field(min_length=1, max_length=64)
    maximum_vehicle_length: PositiveDecimal | None = None
    maximum_vehicle_width: PositiveDecimal | None = None
    maximum_vehicle_height: PositiveDecimal | None = None
    maximum_vehicle_weight: PositiveDecimal | None = None
    weight_unit_id: UUID | None = None
    maximum_expected_pallets: int | None = Field(default=None, ge=1)
    simultaneous_vehicle_capacity: int = Field(default=1, ge=1, le=100)
    refrigeration_capable: bool = False
    temperature_control_capable: bool = False
    hazardous_declared_capable: bool = False
    oversized_capable: bool = False
    high_value_capable: bool = False
    dock_leveler_available: bool = False
    shelter_available: bool = False
    inspection_space_available: bool = False
    notes: str | None = None


class WarehouseDockUpdate(CommandModel):
    row_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    physical_zone: str | None = Field(default=None, max_length=120)
    warehouse_location_id: UUID | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    maximum_vehicle_length: PositiveDecimal | None = None
    maximum_vehicle_width: PositiveDecimal | None = None
    maximum_vehicle_height: PositiveDecimal | None = None
    maximum_vehicle_weight: PositiveDecimal | None = None
    weight_unit_id: UUID | None = None
    maximum_expected_pallets: int | None = Field(default=None, ge=1)
    simultaneous_vehicle_capacity: int | None = Field(default=None, ge=1, le=100)
    refrigeration_capable: bool | None = None
    temperature_control_capable: bool | None = None
    hazardous_declared_capable: bool | None = None
    oversized_capable: bool | None = None
    high_value_capable: bool | None = None
    dock_leveler_available: bool | None = None
    shelter_available: bool | None = None
    inspection_space_available: bool | None = None
    notes: str | None = None


class WarehouseDockResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    code: str
    normalized_code: str
    name: str
    description: str | None
    resource_type: str
    operation_direction: str
    status: str
    physical_zone: str | None
    warehouse_location_id: UUID | None
    timezone: str
    maximum_vehicle_length: Decimal | None
    maximum_vehicle_width: Decimal | None
    maximum_vehicle_height: Decimal | None
    maximum_vehicle_weight: Decimal | None
    weight_unit_id: UUID | None
    maximum_expected_pallets: int | None
    simultaneous_vehicle_capacity: int
    refrigeration_capable: bool
    temperature_control_capable: bool
    hazardous_declared_capable: bool
    oversized_capable: bool
    high_value_capable: bool
    dock_leveler_available: bool
    shelter_available: bool
    inspection_space_available: bool
    notes: str | None
    created_by: UUID
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
    row_version: int


class WarehouseDockSummary(ORMResponse):
    id: UUID
    warehouse_id: UUID
    code: str
    name: str
    resource_type: str
    operation_direction: str
    status: str
    simultaneous_vehicle_capacity: int


class WarehouseDockCapabilityCreate(CommandModel):
    capability_code: str = Field(min_length=1, max_length=60)
    value_type: str = Field(pattern="^(BOOLEAN|NUMBER|TEXT|CODE_LIST)$")
    value_data: JsonValue
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class WarehouseDockOperatingWindowCreate(CommandModel):
    day_of_week: int = Field(ge=0, le=6)
    start_local_time: time
    end_local_time: time
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_order(self) -> "WarehouseDockOperatingWindowCreate":
        if self.start_local_time >= self.end_local_time:
            raise ValueError("start_local_time must be earlier than end_local_time")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        return self


class WarehouseDockOperatingWindowUpdate(CommandModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_local_time: time | None = None
    end_local_time: time | None = None
    effective_from: date | None = None
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_order(self) -> "WarehouseDockOperatingWindowUpdate":
        if (
            self.start_local_time is not None
            and self.end_local_time is not None
            and self.start_local_time >= self.end_local_time
        ):
            raise ValueError("start_local_time must be earlier than end_local_time")
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to must not precede effective_from")
        return self


class WarehouseDockBlackoutCreate(CommandModel):
    starts_at: datetime
    ends_at: datetime
    reason_code: str = Field(min_length=1, max_length=40)
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_order(self) -> "WarehouseDockBlackoutCreate":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be earlier than ends_at")
        return self


class WarehouseDockOperationalStatusResponse(BaseModel):
    dock_id: UUID
    operational_status: str
    active_assignments: int
    capacity: int
    blackout_active: bool
    within_operating_window: bool | None
    reasons: list[str]
    server_time: datetime


class WarehouseDockAvailabilityResponse(BaseModel):
    dock_id: UUID
    available: bool
    operational_status: str
    capacity: int
    occupied_slots: int
    available_slots: int
    reasons: list[str]
    server_time: datetime


class InboundDockQueueCreate(CommandModel):
    gate_check_in_id: UUID
    priority: QueuePriority = QueuePriority.NORMAL
    priority_reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def urgent_requires_reason(self) -> "InboundDockQueueCreate":
        if self.priority in {QueuePriority.URGENT, QueuePriority.SAFETY_CRITICAL} and not self.priority_reason:
            raise ValueError("priority_reason is required for urgent priorities")
        return self


class InboundDockQueueResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    gate_check_in_id: UUID
    appointment_id: UUID | None
    arrival_notice_id: UUID | None
    vehicle_id: UUID | None
    observed_plate_snapshot: str
    supplier_snapshot: JsonObject | None
    carrier_snapshot: JsonObject | None
    priority: str
    priority_reason: str | None
    queue_status: str
    gate_cleared_at: datetime
    queued_at: datetime
    ready_for_assignment_at: datetime | None
    assigned_at: datetime | None
    removed_at: datetime | None
    removal_reason: str | None
    row_version: int


class InboundDockQueuePriorityChangeRequest(CommandModel):
    priority: QueuePriority
    reason: str = Field(min_length=3, max_length=2000)
    row_version: int = Field(ge=1)


class ReasonRequest(CommandModel):
    reason: str = Field(min_length=3, max_length=2000)
    row_version: int | None = Field(default=None, ge=1)


class DockRequestedInterval(CommandModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_order(self) -> "DockRequestedInterval":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be earlier than ends_at")
        return self


class DockAssignmentPlanRequest(CommandModel):
    gate_check_in_id: UUID
    proposed_dock_id: UUID | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=10080)
    assignment_mode: AssignmentMode = AssignmentMode.ASSISTED
    priority: QueuePriority = QueuePriority.NORMAL
    requested_interval: DockRequestedInterval | None = None
    required_capabilities: list[str] = Field(default_factory=list, max_length=50)


class DockCompatibilityResult(BaseModel):
    dock_id: UUID
    compatibility_status: str
    blocking_reasons: list[str]
    warnings: list[str]
    matched_capabilities: list[str]
    missing_information: list[str]
    availability_status: str
    recommendation_score: int
    explanation: list[str]


class DockAssignmentPlanResponse(BaseModel):
    plan_id: UUID
    gate_check_in_id: UUID
    eligible_docks: list[DockCompatibilityResult]
    recommendation: DockCompatibilityResult | None
    incompatibilities: list[DockCompatibilityResult]
    conflicts: list[str]
    warnings: list[str]
    assignment_hash: str
    active_queue_position: int | None
    expires_at: datetime
    server_time: datetime


class DockAssignmentCreate(CommandModel):
    gate_check_in_id: UUID
    dock_id: UUID
    assignment_mode: AssignmentMode = AssignmentMode.MANUAL
    assignment_reason: str = Field(min_length=3, max_length=2000)
    assignment_hash: str = Field(min_length=64, max_length=64)


class DockAssignmentPlanExecuteRequest(CommandModel):
    dock_id: UUID
    assignment_reason: str = Field(min_length=3, max_length=2000)


class DockAssignmentResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    dock_id: UUID
    queue_entry_id: UUID
    gate_check_in_id: UUID
    appointment_id: UUID | None
    arrival_notice_id: UUID | None
    vehicle_id: UUID | None
    observed_plate_snapshot: str
    status: str
    assignment_mode: str
    assignment_reason: str
    compatibility_snapshot: JsonObject
    assignment_hash: str
    planned_start: datetime | None
    planned_end: datetime | None
    capacity_slot: int
    assigned_at: datetime
    assigned_by_user_id: UUID
    assigned_by_snapshot: JsonObject
    movement_started_at: datetime | None
    dock_arrived_at: datetime | None
    released_at: datetime | None
    released_by_user_id: UUID | None
    cancellation_reason: str | None
    reassigned_from_assignment_id: UUID | None
    superseded_by_assignment_id: UUID | None
    created_at: datetime
    updated_at: datetime
    row_version: int


class DockAssignmentSummary(ORMResponse):
    id: UUID
    dock_id: UUID
    gate_check_in_id: UUID
    vehicle_id: UUID | None
    observed_plate_snapshot: str
    status: str
    assigned_at: datetime
    dock_arrived_at: datetime | None
    released_at: datetime | None


class DockAssignmentReassignRequest(CommandModel):
    new_dock_id: UUID
    reason: str = Field(min_length=3, max_length=2000)
    assignment_hash: str = Field(min_length=64, max_length=64)
    row_version: int = Field(ge=1)


class DockAssignmentCapabilities(BaseModel):
    assignment_id: UUID
    status: str
    capabilities: list[str]
    server_time: datetime


class UnloadingOperationCreate(CommandModel):
    unloading_method: UnloadingMethod
    notes: str | None = Field(default=None, max_length=4000)


class UnloadingOperationResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    dock_id: UUID
    dock_assignment_id: UUID
    gate_check_in_id: UUID
    appointment_id: UUID | None
    arrival_notice_id: UUID | None
    operation_code: str
    status: str
    readiness_status: str
    unloading_method: str
    expected_load_summary: JsonObject | None
    special_requirements_snapshot: JsonObject | None
    started_at: datetime | None
    started_by_user_id: UUID | None
    started_by_snapshot: JsonObject | None
    completed_at: datetime | None
    completed_by_user_id: UUID | None
    completed_by_snapshot: JsonObject | None
    aborted_at: datetime | None
    aborted_by_user_id: UUID | None
    abort_reason: str | None
    total_pause_seconds: int
    gross_duration_seconds: int | None
    net_duration_seconds: int | None
    release_required: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    row_version: int


class UnloadingOperationSummary(ORMResponse):
    id: UUID
    operation_code: str
    dock_id: UUID
    dock_assignment_id: UUID
    status: str
    readiness_status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_pause_seconds: int


class UnloadingOperationCapabilities(BaseModel):
    operation_id: UUID
    status: str
    readiness_status: str
    capabilities: list[str]
    server_time: datetime


class UnloadingReadinessCheckRequest(CommandModel):
    check_definition_id: UUID
    result: CheckResult
    observation: str | None = Field(default=None, max_length=2000)
    evidence_file_id: UUID | None = None


class UnloadingCompletionCheckRequest(CommandModel):
    check_definition_id: UUID
    result: CheckResult
    observation: str | None = Field(default=None, max_length=2000)


class UnloadingResponsibleCreate(CommandModel):
    responsibility_type: ResponsibilityType
    user_id: UUID | None = None
    business_partner_id: UUID | None = None
    team_reference_id: UUID | None = None
    exception_reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_authority(self) -> "UnloadingResponsibleCreate":
        refs = [self.user_id, self.business_partner_id, self.team_reference_id]
        if sum(value is not None for value in refs) != 1:
            raise ValueError("exactly one responsible reference is required")
        if self.business_partner_id is not None and self.responsibility_type != ResponsibilityType.EXTERNAL_UNLOADING_CONTRACTOR:
            raise ValueError("business_partner_id is only valid for an external contractor")
        return self


class UnloadingEquipmentCreate(CommandModel):
    equipment_reference_id: UUID | None = None
    equipment_type: str = Field(
        pattern="^(FORKLIFT|PALLET_JACK|CONVEYOR|DOCK_LEVELER|CRANE_DECLARED|HAND_TRUCK|OTHER)$"
    )
    source_type: str = Field(pattern="^(APPROVED_CATALOG|CONTROLLED_REFERENCE)$")
    identifier_snapshot: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def require_controlled_reference(self) -> "UnloadingEquipmentCreate":
        if self.equipment_reference_id is None and self.identifier_snapshot is None:
            raise ValueError("equipment_reference_id or identifier_snapshot is required")
        return self


class UnloadingSealOpeningRequest(CommandModel):
    opening_status: str = Field(min_length=1, max_length=40)
    witnessed_by_user_id: UUID | None = None
    photo_file_id: UUID | None = None
    observation: str | None = Field(default=None, max_length=2000)


class UnloadingPauseRequest(CommandModel):
    reason_code: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=3, max_length=2000)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    evidence_file_id: UUID | None = None

    @model_validator(mode="after")
    def high_requires_evidence(self) -> "UnloadingPauseRequest":
        if self.severity in {"HIGH", "CRITICAL"} and self.evidence_file_id is None:
            raise ValueError("evidence_file_id is required for high severity pauses")
        return self


class UnloadingResumeRequest(CommandModel):
    resolution: str = Field(min_length=3, max_length=2000)


class UnloadingAbortRequest(CommandModel):
    reason: str = Field(min_length=3, max_length=2000)
    evidence_file_id: UUID | None = None


class UnloadingCompleteRequest(CommandModel):
    completion_note: str | None = Field(default=None, max_length=2000)


class DockOperationalTimeCorrectionCreate(CommandModel):
    field_code: str = Field(min_length=1, max_length=60)
    proposed_timestamp: datetime
    reason: str = Field(min_length=3, max_length=2000)
    evidence_file_id: UUID | None = None


class DockOperationExportRequest(CommandModel):
    export_format: str = Field(pattern="^(CSV|XLSX|PDF)$")
    warehouse_id: UUID | None = None
    dock_id: UUID | None = None
    unloading_status: str | None = Field(default=None, max_length=30)
    started_from: datetime | None = None
    started_to: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self) -> "DockOperationExportRequest":
        if self.started_from and self.started_to and self.started_from > self.started_to:
            raise ValueError("started_from must not be later than started_to")
        return self


class DockOperationExportResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID | None
    export_format: str
    filters: JsonObject
    status: str
    requested_by: UUID
    file_asset_id: UUID | None
    error_detail: str | None
    created_at: datetime
    completed_at: datetime | None


class DockOperationIntegrityResponse(BaseModel):
    operation_id: UUID
    valid: bool
    manifest_hashes: JsonObject
    alerts: list[str]
    verified_at: datetime


class UnloadingMetricsResponse(BaseModel):
    operation_id: UUID
    metrics: dict[str, int | str | None]
    server_time: datetime


class ReceivingScanPreparationResponse(BaseModel):
    unloading_operation_id: UUID
    dock_assignment_id: UUID
    gate_check_in_id: UUID
    cpv_code: str | None
    appointment_id: UUID | None
    cit_code: str | None
    warehouse_id: UUID
    dock_id: UUID
    supplier_summary: JsonObject | None
    carrier_summary: JsonObject | None
    vehicle_summary: JsonObject | None
    observed_plate: str
    purchase_order_references: list[JsonObject]
    expected_lines: list[JsonObject]
    transport_documents: list[JsonObject]
    seal_opening_summary: JsonObject | None
    unloading_started_at: datetime
    unloading_completed_at: datetime
    unloading_status: str
    responsible_summary: list[JsonObject]
    operational_warnings: list[str]
    data_quality_status: str
    receiving_capabilities_future: list[str]


class PageResponse(BaseModel):
    items: list[dict[str, object]]
    total: int
    page: int
    page_size: int
    server_time: datetime
