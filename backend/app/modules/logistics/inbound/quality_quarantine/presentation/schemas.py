"""Phase 042 — Pydantic schemas for quality quarantine module."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class CommandModel(BaseModel):
    model_config = {"extra": "forbid"}

    @field_validator("*", mode="before")
    @classmethod
    def reject_float(cls, v: Any) -> Any:
        if isinstance(v, float):
            raise ValueError("Use strings for decimal values, not floats")
        return v


class ORMResponse(BaseModel):
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Allocation schemas
# ---------------------------------------------------------------------------

class DispositionMaterializeRequest(CommandModel):
    inbound_receipt_id: UUID
    inbound_receipt_revision_id: UUID
    inbound_received_line_id: UUID
    expected_line_id: UUID | None = None
    purchase_order_id: UUID | None = None
    purchase_order_line_id: UUID | None = None
    supplier_business_partner_id: UUID
    product_id: UUID
    product_version_id: UUID | None = None
    sku_snapshot: str | None = None
    product_name_snapshot: str | None = None
    quantity: str
    unit_id: UUID
    base_quantity: str
    lot_observation_ids: list[str] | None = None
    serial_observation_ids: list[str] | None = None
    expiration_observation_ids: list[str] | None = None
    difference_case_ids: list[str] | None = None


class AllocationResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    inbound_receipt_id: UUID
    inbound_received_line_id: UUID
    product_id: UUID
    product_name_snapshot: str | None = None
    quantity: str
    unit_id: UUID
    base_quantity: str
    allocation_status: str
    availability_class: str
    quality_status: str
    created_at: datetime


class AllocationSummary(ORMResponse):
    id: UUID
    allocation_status: str
    availability_class: str
    quality_status: str
    quantity: str
    unit_id: UUID
    product_name_snapshot: str | None = None


class SplitRequest(CommandModel):
    first_quantity: str
    first_base_quantity: str
    split_reason: str


class SplitResponse(BaseModel):
    split_id: str
    source_allocation_id: str
    first_child_id: str
    second_child_id: str
    first_quantity: str
    second_quantity: str


# ---------------------------------------------------------------------------
# Quarantine Case schemas
# ---------------------------------------------------------------------------

class QuarantineCaseCreate(CommandModel):
    source_type: str
    inbound_receipt_id: UUID
    product_id: UUID
    product_version_id: UUID | None = None
    quarantine_reason: str | None = None
    reason_description: str | None = None


class QuarantineCaseFromAllocationCreate(CommandModel):
    allocation_id: UUID
    quarantine_reason: str | None = None
    reason_description: str | None = None


class QuarantineCaseResponse(ORMResponse):
    id: UUID
    quarantine_code: str
    source_type: str
    inbound_receipt_id: UUID
    product_id: UUID
    status: str
    severity: str
    quarantine_reason: str | None = None
    quality_result: str | None = None
    quality_decision_status: str
    release_status: str
    physical_segregation_status: str
    opened_at: datetime | None = None
    created_at: datetime


class QuarantineCaseSummary(ORMResponse):
    id: UUID
    quarantine_code: str
    status: str
    severity: str
    quality_result: str | None = None
    release_status: str


class QuarantineCapabilities(BaseModel):
    can_activate: bool
    can_cancel: bool
    can_close: bool
    can_materialize_inspection: bool
    can_request_release: bool
    can_request_rejection: bool


# ---------------------------------------------------------------------------
# Zone schemas
# ---------------------------------------------------------------------------

class ZoneCreate(CommandModel):
    warehouse_location_id: UUID
    code: str
    name: str
    allowed_product_categories: list[str] | None = None
    temperature_capabilities: dict[str, Any] | None = None
    hazardous_declared_capable: bool = False
    maximum_capacity_reference: str | None = None
    capacity_unit_id: UUID | None = None
    priority: int = 0
    instructions: str | None = None


class ZoneUpdate(CommandModel):
    name: str | None = None
    status: str | None = None
    allowed_product_categories: list[str] | None = None
    temperature_capabilities: dict[str, Any] | None = None
    hazardous_declared_capable: bool | None = None
    maximum_capacity_reference: str | None = None
    priority: int | None = None
    instructions: str | None = None


class ZoneResponse(ORMResponse):
    id: UUID
    code: str
    name: str
    status: str
    warehouse_id: UUID
    warehouse_location_id: UUID
    priority: int
    hazardous_declared_capable: bool


# ---------------------------------------------------------------------------
# Placement schemas
# ---------------------------------------------------------------------------

class PlacementCreate(CommandModel):
    allocation_id: UUID
    quarantine_zone_id: UUID
    quantity: str
    unit_id: UUID
    base_quantity: str
    observation: str | None = None


class PlacementResponse(ORMResponse):
    id: UUID
    quarantine_case_id: UUID
    allocation_id: UUID
    quarantine_zone_id: UUID
    placement_status: str
    quantity: str
    unit_id: UUID
    confirmed_at: datetime | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Inspection schemas
# ---------------------------------------------------------------------------

class InspectionCreate(CommandModel):
    quarantine_case_id: UUID
    allocation_id: UUID


class InspectionResponse(ORMResponse):
    id: UUID
    inspection_code: str
    quarantine_case_id: UUID
    allocation_id: UUID
    status: str
    overall_result: str
    required_control_count: int
    completed_control_count: int
    failed_control_count: int
    evidence_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class InspectionSummary(ORMResponse):
    id: UUID
    inspection_code: str
    status: str
    overall_result: str


class InspectionCapabilities(BaseModel):
    can_start: bool
    can_pause: bool
    can_resume: bool
    can_complete: bool
    can_cancel: bool


# ---------------------------------------------------------------------------
# Control schemas
# ---------------------------------------------------------------------------

class ControlResponse(ORMResponse):
    id: UUID
    inspection_id: UUID
    control_code: str
    name_snapshot: str
    control_type: str
    order_index: int
    required: bool
    blocking_on_fail: bool
    status: str


class ControlResultCreate(CommandModel):
    result_status: str
    boolean_value: bool | None = None
    decimal_value: str | None = None
    integer_value: int | None = None
    text_value: str | None = None
    option_value: str | None = None
    unit_id: UUID | None = None
    observation: str | None = None
    evidence_complete: bool = False


class ControlResultResponse(ORMResponse):
    id: UUID
    inspection_control_id: UUID
    result_status: str
    boolean_value: bool | None = None
    decimal_value: str | None = None
    measured_by: UUID
    measured_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Measurement schemas
# ---------------------------------------------------------------------------

class MeasurementCreate(CommandModel):
    inspection_control_id: UUID
    measurement_type: str
    measured_value: str
    unit_id: UUID
    device_reference: str | None = None
    calibration_reference: str | None = None
    observation: str | None = None


class MeasurementResponse(ORMResponse):
    id: UUID
    inspection_id: UUID
    measurement_type: str
    measured_value: str
    unit_id: UUID
    tolerance_result: str | None = None
    measured_by: UUID
    measured_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Sample schemas
# ---------------------------------------------------------------------------

class SampleSetCreate(CommandModel):
    sampling_plan_id: UUID | None = None
    population_quantity: str
    population_unit_id: UUID
    required_sample_size: int
    sample_unit: str | None = None
    selection_method: str | None = None


class SampleSetResponse(ORMResponse):
    id: UUID
    inspection_id: UUID
    population_quantity: str
    required_sample_size: int
    status: str
    created_at: datetime


class SampleReferenceCreate(CommandModel):
    source_reference_type: str
    inbound_received_line_id: UUID | None = None
    lot_observation_id: UUID | None = None
    serial_observation_id: UUID | None = None
    package_ordinal: int | None = None
    operator_reference: str | None = None


# ---------------------------------------------------------------------------
# Certificate schemas
# ---------------------------------------------------------------------------

class CertificateReviewCreate(CommandModel):
    certificate_requirement_id: UUID | None = None
    requirement_code: str
    document_file_id: UUID | None = None
    review_status: str
    issuer_observed: str | None = None
    issue_date_observed: datetime | None = None
    expiration_date_observed: datetime | None = None
    reference_number_observed: str | None = None
    observation: str | None = None


class CertificateReviewResponse(ORMResponse):
    id: UUID
    inspection_id: UUID
    requirement_code: str
    review_status: str
    issuer_observed: str | None = None
    reviewed_by: UUID
    reviewed_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Evidence schemas
# ---------------------------------------------------------------------------

class EvidenceLinkCreate(CommandModel):
    inspection_control_id: UUID | None = None
    file_asset_id: UUID
    file_version_id: UUID | None = None
    evidence_type: str
    description: str | None = None
    classification: str = "STANDARD"


class EvidenceResponse(ORMResponse):
    id: UUID
    inspection_id: UUID
    file_asset_id: UUID
    evidence_type: str
    classification: str
    linked_by: UUID
    linked_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Decision schemas
# ---------------------------------------------------------------------------

class DecisionCreate(CommandModel):
    inspection_id: UUID | None = None
    allocation_id: UUID
    decision_type: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    reason_code: str | None = None
    reason: str | None = None


class DecisionResponse(ORMResponse):
    id: UUID
    quarantine_case_id: UUID
    decision_type: str
    decision_status: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    reason: str | None = None
    proposed_by: UUID
    proposed_at: datetime
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime


class DecisionApprovalRequest(CommandModel):
    decision: str
    reason: str | None = None


# ---------------------------------------------------------------------------
# Release schemas
# ---------------------------------------------------------------------------

class ReleaseRequest(CommandModel):
    allocation_id: UUID
    quality_decision_id: UUID
    release_type: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    release_reason: str | None = None


class ReleaseResponse(ORMResponse):
    id: UUID
    quarantine_case_id: UUID
    allocation_id: UUID
    release_type: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    status: str
    requested_by: UUID
    requested_at: datetime
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    executed_by: UUID | None = None
    executed_at: datetime | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Rejection schemas
# ---------------------------------------------------------------------------

class RejectionRequest(CommandModel):
    allocation_id: UUID
    quality_decision_id: UUID
    rejection_type: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    reason_code: str | None = None
    reason: str | None = None
    future_disposition_recommendation: str | None = None


class RejectionResponse(ORMResponse):
    id: UUID
    quarantine_case_id: UUID
    allocation_id: UUID
    rejection_type: str
    quantity: str
    unit_id: UUID
    base_quantity: str
    status: str
    reason: str | None = None
    future_disposition_recommendation: str | None = None
    requested_by: UUID
    requested_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Reinspection schemas
# ---------------------------------------------------------------------------

class ReinspectionRequestCreate(CommandModel):
    previous_inspection_id: UUID
    reason: str
    additional_evidence_required: bool = False


class ReinspectionRequestResponse(ORMResponse):
    id: UUID
    quarantine_case_id: UUID
    previous_inspection_id: UUID
    reason: str
    status: str
    requested_by: UUID
    requested_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Availability projection schemas
# ---------------------------------------------------------------------------

class AvailabilityResponse(BaseModel):
    allocation_id: UUID
    product_id: UUID
    quantity: str
    unit_id: UUID
    base_quantity: str
    availability_class: str
    quality_status: str
    quarantine_case_id: UUID | None = None
    inspection_id: UUID | None = None
    decision_id: UUID | None = None


class AvailabilitySummaryResponse(BaseModel):
    total_blocked: str
    total_quarantine: str
    total_available_for_putaway: str
    total_rejected: str
    items: list[AvailabilityResponse]


# ---------------------------------------------------------------------------
# Future preparation schemas
# ---------------------------------------------------------------------------

class PutawayPreparationResponse(BaseModel):
    allocation_id: UUID
    product_id: UUID
    quantity: str
    unit_id: UUID
    base_quantity: str
    eligible_for_putaway: bool
    blocking_reasons: list[str]


class FutureMovementPreparationResponse(BaseModel):
    source_allocation_id: UUID
    product_id: UUID
    quantity: str
    event_type: str


class FutureBalancePreparationResponse(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    availability_class: str
    quantity: str
    unit_id: UUID


class FutureTraceabilityPreparationResponse(BaseModel):
    allocation_id: UUID
    product_id: UUID
    observed_lot_references: list[str]
    observed_serial_references: list[str]
    quality_status: str


# ---------------------------------------------------------------------------
# Integrity response
# ---------------------------------------------------------------------------

class IntegrityResponse(BaseModel):
    case_id: UUID
    overall_hash: str
    verified: bool
    components: dict[str, str]
