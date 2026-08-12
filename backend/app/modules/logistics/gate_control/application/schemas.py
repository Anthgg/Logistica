"""Pydantic v2 Schemas for Phase 037 (Gate Control Application Services)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.logistics.documents.rendering.inbound_schemas import mask_sensitive_id
from app.modules.logistics.gate_control.domain.enums import (
    AccessDecision,
    GateEventType,
    GateRecordStatus,
    GateStatus,
    GateType,
    SealStatus,
)


class ApiModel(BaseModel):
    """Base API schema model with standard configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# --- Warehouse Gate DTOs ---

class WarehouseGateCreate(ApiModel):
    """Payload to register a new physical or logical warehouse gate."""

    code: str = Field(..., min_length=2, max_length=50, description="Unique code within organization (e.g. GATE-01)")
    name: str = Field(..., min_length=2, max_length=100, description="Descriptive gate name")
    warehouse_id: UUID = Field(..., description="ID of the physical warehouse facility")
    gate_type: GateType = Field(default=GateType.MAIN_ENTRY, description="Classification of gate")
    status: GateStatus = Field(default=GateStatus.ACTIVE, description="Initial operational status")
    notes: Optional[str] = Field(default=None, description="Optional administrative notes")
    is_active: bool = Field(default=True, description="Active status flag")


class WarehouseGateUpdate(ApiModel):
    """Payload to update an existing warehouse gate."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    gate_type: Optional[GateType] = Field(default=None)
    status: Optional[GateStatus] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    expected_version: Optional[int] = Field(default=None, description="Row version for optimistic concurrency control")


class WarehouseGateResponse(ApiModel):
    """Response DTO representing a warehouse gate."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    warehouse_id: UUID
    gate_type: str
    status: str
    notes: Optional[str] = None
    is_active: bool
    row_version: int
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# --- Gate Preparation & Check-In DTOs ---

class GatePreparationResponse(ApiModel):
    """Expected appointment context retrieved for gate check-in preparation."""

    appointment_id: UUID
    appointment_code: Optional[str] = None
    arrival_notice_id: UUID
    warehouse_id: UUID
    expected_plate: Optional[str] = None
    expected_seal_reference: Optional[str] = None
    expected_driver_dni: Optional[str] = None
    expected_vehicle_id: Optional[UUID] = None
    carrier_partner_id: Optional[UUID] = None
    carrier_name: Optional[str] = None
    appointment_status: str
    guide_references: List[str] = Field(default_factory=list)
    verification_warnings: List[str] = Field(default_factory=list)


class GateCheckInRequest(ApiModel):
    """Payload submitted by security guard upon vehicle arrival at a gate."""

    gate_id: UUID = Field(..., description="ID of gate where vehicle arrived")
    reception_appointment_id: Optional[UUID] = Field(default=None, description="Optional linked appointment ID")
    plate_observed: str = Field(..., min_length=2, max_length=20, description="Observed vehicle license plate")
    seal_status: SealStatus = Field(default=SealStatus.NOT_APPLICABLE, description="Cargo seal status observed")
    driver_dni_raw: Optional[str] = Field(default=None, max_length=50, description="Raw driver identity document")
    driver_license_raw: Optional[str] = Field(default=None, max_length=50, description="Raw driver license number")
    vehicle_id: Optional[UUID] = Field(default=None, description="Optional mapped vehicle ID")
    driver_id: Optional[UUID] = Field(default=None, description="Optional mapped driver ID")
    notes: Optional[str] = Field(default=None, description="Guard observations or notes")


class GateDecisionRequest(ApiModel):
    """Payload to authorize or deny access for a gate record."""

    record_id: UUID = Field(..., description="ID of gate control record to evaluate")
    decision: AccessDecision = Field(..., description="Decision: APPROVED or DENIED")
    rejection_reason: Optional[str] = Field(default=None, description="Required when decision is DENIED")
    expected_version: Optional[int] = Field(default=None, description="Row version for concurrency check")


class GateCheckOutRequest(ApiModel):
    """Payload to record vehicle check-out and departure."""

    record_id: UUID = Field(..., description="ID of gate control record")
    check_out_at: Optional[datetime] = Field(default=None, description="Check-out timestamp (defaults to current time if None)")
    notes: Optional[str] = Field(default=None, description="Check-out notes")
    expected_version: Optional[int] = Field(default=None, description="Row version for concurrency check")


# --- Gate Control Record Output DTOs ---

class GateControlHistoryResponse(ApiModel):
    """Audit log entry for status transitions."""

    id: UUID
    record_id: UUID
    previous_status: Optional[str] = None
    new_status: str
    changed_by_user_id: UUID
    change_reason: str
    created_at: datetime


class GateControlRecordResponse(ApiModel):
    """Response DTO for gate control records with sensitive identity fields masked."""

    id: UUID
    organization_id: UUID
    record_code: str
    gate_id: UUID
    reception_appointment_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    guard_user_id: UUID
    event_type: str
    arrival_at: datetime
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    access_decision: str
    plate_observed: str
    seal_status: str
    driver_dni_masked: str = Field(..., description="Masked DNI for privacy protection")
    driver_license_masked: str = Field(..., description="Masked license number for privacy protection")
    rejection_reason: Optional[str] = None
    document_instance_id: Optional[UUID] = None
    status: str
    row_version: int
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    history_entries: List[GateControlHistoryResponse] = Field(default_factory=list)

    @classmethod
    def from_model(cls, model: Any) -> GateControlRecordResponse:
        """Construct response DTO from ORM model with sensitive field masking."""
        history = getattr(model, "history_entries", []) or []
        return cls(
            id=model.id,
            organization_id=model.organization_id,
            record_code=model.record_code,
            gate_id=model.gate_id,
            reception_appointment_id=model.reception_appointment_id,
            vehicle_id=model.vehicle_id,
            driver_id=model.driver_id,
            guard_user_id=model.guard_user_id,
            event_type=str(model.event_type),
            arrival_at=model.arrival_at,
            check_in_at=model.check_in_at,
            check_out_at=model.check_out_at,
            access_decision=str(model.access_decision),
            plate_observed=model.plate_observed,
            seal_status=str(model.seal_status),
            driver_dni_masked=mask_sensitive_id(getattr(model, "driver_dni_raw", None), visible_end=2),
            driver_license_masked=mask_sensitive_id(getattr(model, "driver_license_raw", None), visible_end=2),
            rejection_reason=model.rejection_reason,
            document_instance_id=model.document_instance_id,
            status=str(model.status),
            row_version=model.row_version,
            content_hash=model.content_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
            history_entries=[
                GateControlHistoryResponse(
                    id=entry.id,
                    record_id=entry.record_id,
                    previous_status=entry.previous_status,
                    new_status=str(entry.new_status),
                    changed_by_user_id=entry.changed_by_user_id,
                    change_reason=entry.change_reason,
                    created_at=entry.created_at,
                )
                for entry in history
            ],
        )
