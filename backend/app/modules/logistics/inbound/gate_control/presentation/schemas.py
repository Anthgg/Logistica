"""Pydantic v2 schemas for Phase 037 Gate Control API layer.

Conventions:
- Create schemas: only fields the CLIENT can supply.
- Response schemas: fields the API exposes (never storage keys, signed URLs,
  full document numbers, photos, full license numbers).
- guard_user_id, supervisor_user_id, arrived_at, decision fields:
  NEVER accepted from the request body.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# WarehouseGate
# ─────────────────────────────────────────────────────────────────────────────

class WarehouseGateCreate(BaseModel):
    warehouse_id: UUID
    branch_id: UUID
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    gate_type: str = Field(default="VEHICLE_ENTRY")
    direction_policy: str = Field(default="ENTRY_ONLY")
    timezone: str = Field(..., min_length=1, max_length=64)
    instructions: Optional[str] = None


class WarehouseGateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = None
    gate_type: Optional[str] = None
    direction_policy: Optional[str] = None
    timezone: Optional[str] = None
    instructions: Optional[str] = None
    row_version: int = Field(..., ge=1)


class WarehouseGateResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    gate_type: str
    direction_policy: str
    timezone: str
    status: str
    active_verification_policy_version_id: Optional[UUID] = None
    instructions: Optional[str] = None
    created_by: UUID
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    row_version: int

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Verification Policy
# ─────────────────────────────────────────────────────────────────────────────

class GateVerificationPolicyCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    scope_type: str = Field(default="ORGANIZATION")
    warehouse_id: Optional[UUID] = None
    gate_id: Optional[UUID] = None


class GateVerificationPolicyVersionCreate(BaseModel):
    late_tolerance_minutes: int = Field(default=30, ge=0)
    early_tolerance_minutes: int = Field(default=60, ge=0)
    walk_in_allowed: bool = False
    photo_requirements: dict = Field(default_factory=dict)
    seal_requirement: str = "REQUIRED"
    document_requirements: dict = Field(default_factory=dict)
    vehicle_mismatch_policy: str = "BLOCK"
    driver_mismatch_policy: str = "BLOCK"
    license_expired_policy: str = "BLOCK"
    verification_expired_policy: str = "BLOCK"
    missing_document_policy: str = "WARN"
    broken_seal_policy: str = "BLOCK"
    decision_matrix: dict = Field(default_factory=dict)


class GateVerificationCheckCreate(BaseModel):
    check_code: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    category: str
    order_index: int = Field(default=0, ge=0)
    required: bool = True
    blocking_on_fail: bool = False
    requires_photo: bool = False
    requires_document: bool = False
    requires_comment_on_fail: bool = True
    allow_supervisor_override: bool = False
    override_step_up_level: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Appointment Resolution
# ─────────────────────────────────────────────────────────────────────────────

class GateAppointmentResolveRequest(BaseModel):
    """All fields optional — at least one must be provided."""
    cit_code: Optional[str] = None
    opaque_qr_payload: Optional[str] = None
    plate: Optional[str] = None
    purchase_order_code: Optional[str] = None
    warehouse_id: UUID

    @model_validator(mode="after")
    def at_least_one_identifier(self) -> "GateAppointmentResolveRequest":
        if not any([self.cit_code, self.opaque_qr_payload, self.plate, self.purchase_order_code]):
            raise ValueError(
                "Se requiere al menos un identificador: cit_code, opaque_qr_payload, plate o purchase_order_code."
            )
        return self


class GateAppointmentResolveResponse(BaseModel):
    appointment_id: Optional[UUID] = None
    appointment_code: Optional[str] = None
    appointment_status: Optional[str] = None
    arrival_notice_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    supplier_summary: Optional[dict] = None
    carrier_summary: Optional[dict] = None
    gate_preparation: Optional[dict] = None
    gate_eligibility: str = "ELIGIBLE"
    warnings: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    server_time: datetime = Field(default_factory=lambda: datetime.now())


# ─────────────────────────────────────────────────────────────────────────────
# GateCheckIn Create
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInCreate(BaseModel):
    """Fields the client can supply when initiating a gate check-in.

    CRITICAL — fields NEVER accepted from client:
      guard_user_id, arrived_at, decision, verification_passed,
      supervisor_user_id, step_up_passed, biometric_score.
    """
    gate_id: UUID
    appointment_id: Optional[UUID] = None
    cit_code: Optional[str] = None
    opaque_qr_payload: Optional[str] = None

    @model_validator(mode="after")
    def has_appointment_reference(self) -> "GateCheckInCreate":
        if not any([self.appointment_id, self.cit_code, self.opaque_qr_payload]):
            raise ValueError(
                "Se requiere appointment_id, cit_code u opaque_qr_payload."
            )
        return self


class GateWalkInCreate(BaseModel):
    """Walk-in (unscheduled) check-in — requires elevated permissions."""
    gate_id: UUID
    reason: str = Field(..., min_length=5)
    supplier_id: UUID
    carrier_id: Optional[UUID] = None
    carrier_exception_reason: Optional[str] = None
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# GateCheckIn Responses
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInSummary(BaseModel):
    id: UUID
    cpv_code: Optional[str] = None
    cit_code: Optional[str] = None
    supplier_summary: Optional[dict] = None
    carrier_summary: Optional[dict] = None
    warehouse_summary: Optional[dict] = None
    gate_summary: Optional[dict] = None
    expected_plate: Optional[str] = None
    observed_plate: Optional[str] = None
    driver_summary_redacted: Optional[dict] = None
    arrived_at: Optional[datetime] = None
    arrival_classification: Optional[str] = None
    status: str
    decision: Optional[str] = None
    seal_status: Optional[str] = None
    failed_check_count: int = 0
    exception_count: int = 0
    guard_summary: Optional[dict] = None
    updated_at: datetime
    capabilities: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class GateCheckInCapabilities(BaseModel):
    check_in_id: UUID
    status: str
    can_record_arrival: bool = False
    can_start_verification: bool = False
    can_submit_vehicle_inspection: bool = False
    can_submit_driver_inspection: bool = False
    can_submit_document: bool = False
    can_submit_seal_inspection: bool = False
    can_capture_photo: bool = False
    can_complete_check_result: bool = False
    can_request_exception: bool = False
    can_authorize_entry: bool = False
    can_authorize_with_observations: bool = False
    can_deny_entry: bool = False
    can_hold: bool = False
    can_request_supervisor: bool = False
    can_resume: bool = False
    can_cancel: bool = False
    can_complete: bool = False
    can_issue_document: bool = False
    can_preview_document: bool = False
    can_request_correction: bool = False
    server_time: datetime = Field(default_factory=lambda: datetime.now())


class GateCheckInResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    gate_id: UUID
    appointment_id: Optional[UUID] = None
    arrival_notice_id: Optional[UUID] = None
    appointment_code_snapshot: Optional[str] = None
    check_in_code: Optional[str] = None
    document_instance_id: Optional[UUID] = None
    status: str
    source_type: str
    arrival_classification: str
    arrived_at: Optional[datetime] = None
    recorded_at: Optional[datetime] = None
    gate_timezone: str
    check_started_at: Optional[datetime] = None
    verification_completed_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    check_completed_at: Optional[datetime] = None
    guard_user_id: UUID
    guard_snapshot: Optional[dict] = None
    supervisor_user_id: Optional[UUID] = None
    supplier_snapshot: Optional[dict] = None
    carrier_snapshot: Optional[dict] = None
    verification_policy_version_id: Optional[UUID] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    entry_authorized_at: Optional[datetime] = None
    entry_denied_at: Optional[datetime] = None
    hold_reason: Optional[str] = None
    exception_count: int = 0
    failed_check_count: int = 0
    warning_count: int = 0
    current_revision_number: int = 1
    active_revision_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    row_version: int

    class Config:
        from_attributes = True


class GateCheckInListResponse(BaseModel):
    items: list[GateCheckInSummary]
    total: int
    page: int
    page_size: int


class GateCheckInValidationResponse(BaseModel):
    check_in_id: UUID
    can_authorize: bool
    can_authorize_with_observations: bool
    blocking_failed_count: int
    blocking_failed: list[str]
    pending_exceptions_count: int
    warnings: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Inspections
# ─────────────────────────────────────────────────────────────────────────────

class GateVehicleInspectionCreate(BaseModel):
    observed_plate: str = Field(..., min_length=1, max_length=20)
    observed_vehicle_id: Optional[UUID] = None
    capture_method: str = "MANUAL_ENTRY"
    visual_condition: Optional[str] = None
    exception_reason: Optional[str] = None


class GateDriverInspectionCreate(BaseModel):
    observed_driver_id: Optional[UUID] = None
    observed_name_snapshot: Optional[str] = None
    observed_document_type: Optional[str] = None
    # Full document number encrypted at application layer
    observed_document_number: Optional[str] = None
    license_number: Optional[str] = None
    license_category: Optional[str] = None
    license_expiration: Optional[datetime] = None
    exception_reason: Optional[str] = None


class GatePresentedDocumentCreate(BaseModel):
    document_kind: str
    expected_reference: Optional[str] = None
    observed_series: Optional[str] = None
    observed_number: Optional[str] = None
    file_asset_id: Optional[UUID] = None
    notes: Optional[str] = None


class GateSealInspectionCreate(BaseModel):
    seal_required: bool = False
    expected_seal_number: Optional[str] = None
    observed_seal_number: Optional[str] = None
    physical_status: str = "NOT_APPLICABLE"
    exception_reason: Optional[str] = None
    photo_file_asset_id: Optional[UUID] = None


class GateVerificationCheckResultCreate(BaseModel):
    check_definition_id: Optional[UUID] = None
    check_code: str = Field(..., min_length=1, max_length=60)
    result: str
    observed_value: Optional[str] = None
    expected_value: Optional[str] = None
    explanation: Optional[str] = None
    evidence_file_ids: Optional[list[UUID]] = None


class GateVerificationExceptionCreate(BaseModel):
    check_result_id: Optional[UUID] = None
    exception_type: str
    risk_level: str = "MEDIUM"
    reason: str = Field(..., min_length=5)
    evidence_file_id: Optional[UUID] = None


class GateEntryDecisionRequest(BaseModel):
    """Request body for authorize/deny commands.

    CRITICAL — decided_by, decision_at, decision_hash are NEVER accepted
    from the client. They are resolved server-side.
    """
    reason: str = Field(..., min_length=5)
    conditions: Optional[list[str]] = None


class GateCheckInHoldRequest(BaseModel):
    hold_reason: str = Field(..., min_length=5)


class GateCheckInCorrectionCreate(BaseModel):
    field_code: str = Field(..., min_length=1, max_length=60)
    proposed_value: Optional[str] = None
    reason: str = Field(..., min_length=5)
    evidence_file_id: Optional[UUID] = None


class GateCheckInTimeCorrectionCreate(BaseModel):
    proposed_arrived_at: datetime
    reason: str = Field(..., min_length=10)
    evidence_file_id: Optional[UUID] = None


class GateCpvDocumentResponse(BaseModel):
    """Metadata for the immutable CPV and its binary download endpoint."""

    document_instance_id: UUID
    check_in_id: UUID
    document_code: Optional[str] = None
    status: str
    issued_at: Optional[datetime] = None
    snapshot_hash: Optional[str] = None
    download_url: str
    expires_at: Optional[datetime] = None


class GateIntegrityResponse(BaseModel):
    check_in_id: UUID
    revision_hash_valid: bool
    snapshot_hash_valid: bool
    cpv_hash_valid: Optional[bool] = None
    alerts: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=lambda: datetime.now())


class DockAssignmentPreparationResponse(BaseModel):
    """Read-only contract for Phase 038 dock assignment.

    Fields intentionally absent: dock_id, unload_started_at,
    received_quantity, lot, serial, pallet.
    """
    gate_check_in_id: UUID
    cpv_code: Optional[str] = None
    appointment_id: Optional[UUID] = None
    cit_code: Optional[str] = None
    warehouse_id: UUID
    gate_id: UUID
    supplier_summary: Optional[dict] = None
    carrier_summary: Optional[dict] = None
    vehicle_id: Optional[UUID] = None
    observed_plate: Optional[str] = None
    driver_id: Optional[UUID] = None
    arrival_time: Optional[datetime] = None
    gate_clearance_status: Optional[str] = None
    clearance_conditions: Optional[dict] = None
    seal_status: Optional[str] = None
    document_summary: Optional[dict] = None
    special_requirements: Optional[Any] = None
    expected_pallet_count: Optional[int] = None
    expected_package_count: Optional[int] = None
    expected_weight: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    capabilities_future: list[str] = Field(default_factory=list)


__all__ = [
    "WarehouseGateCreate",
    "WarehouseGateUpdate",
    "WarehouseGateResponse",
    "GateVerificationPolicyCreate",
    "GateVerificationPolicyVersionCreate",
    "GateVerificationCheckCreate",
    "GateAppointmentResolveRequest",
    "GateAppointmentResolveResponse",
    "GateCheckInCreate",
    "GateWalkInCreate",
    "GateCheckInSummary",
    "GateCheckInCapabilities",
    "GateCheckInResponse",
    "GateCheckInListResponse",
    "GateCheckInValidationResponse",
    "GateVehicleInspectionCreate",
    "GateDriverInspectionCreate",
    "GatePresentedDocumentCreate",
    "GateSealInspectionCreate",
    "GateVerificationCheckResultCreate",
    "GateVerificationExceptionCreate",
    "GateEntryDecisionRequest",
    "GateCheckInHoldRequest",
    "GateCheckInCorrectionCreate",
    "GateCheckInTimeCorrectionCreate",
    "GateCpvDocumentResponse",
    "GateIntegrityResponse",
    "DockAssignmentPreparationResponse",
]
