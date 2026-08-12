"""Pydantic v2 schemas for Delivery Document contexts and Package Manifests (Phase 019).

Covers: POD, EP, RECH, and TransportDeliveryDocumentPackageManifest
Phase boundaries:
  - Receiver and OTP verification snapshots
  - Delivery quantities balances (EP)
  - Rejection reasons (RECH)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.logistics.documents.rendering.dispatch_schemas import (
    VehicleSnapshot,
    DriverSnapshot,
)
from app.modules.logistics.documents.rendering.transport_schemas import (
    CoordinatesSnapshot,
)


# ---------------------------------------------------------------------------
# 1. Receiver, OTP, and Evidence Snapshots
# ---------------------------------------------------------------------------

class ReceiverSnapshot(BaseModel):
    """Receiver details snapshot (PENDING_PHASE_071)."""
    model_config = ConfigDict(extra="ignore")

    full_name: str
    document_type: str | None = "DNI"
    document_number_masked: str | None = None
    role_or_relationship: str | None = None  # SELF | REPRESENTATIVE | SECURITY | NEIGHBOR | OTHER
    company: str | None = None
    phone_masked: str | None = None
    email_masked: str | None = None
    identity_verification_status: str = "PENDING"  # PENDING | VERIFIED | FAILED
    authorization_status: str = "NOT_EVALUATED"  # NOT_EVALUATED | AUTHORIZED | UNAUTHORIZED


class OTPVerificationSnapshot(BaseModel):
    """OTP Verification details (PENDING_PHASE_072)."""
    model_config = ConfigDict(extra="ignore")

    required: bool = False
    attempted: bool = False
    result: str = "NOT_REQUIRED"  # NOT_REQUIRED | NOT_ATTEMPTED | VERIFIED | FAILED | EXPIRED | LOCKED | UNAVAILABLE | DEMO_ONLY
    verified_at: str | None = None
    channel: str | None = None  # SMS | WHATSAPP | EMAIL | OTHER
    attempts_count: int = Field(default=0, ge=0)
    policy_reference: str | None = None


class DeliveryPhotoEvidenceSnapshot(BaseModel):
    """Photo evidence details (PENDING_PHASE_030)."""
    model_config = ConfigDict(extra="ignore")

    evidence_type: str = "DELIVERED_GOODS"  # DELIVERED_GOODS | RECEIVER | SIGNATURE | PROPERTY | DAMAGED_GOODS | REJECTION | DOCUMENT | OTHER
    file_reference: str
    filename: str
    mime_type: str = "image/jpeg"
    captured_at: str | None = None
    coordinates: CoordinatesSnapshot | None = None
    accuracy_meters: Decimal | None = None
    hash: str | None = None
    validation_status: str = "PENDING"  # PENDING | VALID | INVALID
    is_demo_data: bool = False


class DeliveryEvidenceValidationSnapshot(BaseModel):
    """Evidence validity results (PENDING_PHASE_074)."""
    model_config = ConfigDict(extra="ignore")

    GPS_present: bool = False
    GPS_accuracy_acceptable: bool = False
    timestamp_present: bool = False
    timestamp_consistent: bool = False
    photo_present: bool = False
    signature_present: bool = False
    OTP_present: bool = False
    stop_relation_valid: bool = False
    evidence_consistency: str = "NOT_EVALUATED"
    validation_status: str = "NOT_EVALUATED"  # NOT_EVALUATED | SUFFICIENT | PARTIALLY_SUFFICIENT | INSUFFICIENT | CONFLICTING | DEMO_ONLY
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. Line snapshots & Quantity Validator
# ---------------------------------------------------------------------------

class DeliveryLineSnapshot(BaseModel):
    """Snapshot of a delivery transaction line."""
    model_config = ConfigDict(extra="ignore")

    line_number: int = Field(..., ge=1)
    product_snapshot: dict[str, Any]
    planned_quantity: Decimal = Field(..., ge=0)
    delivered_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    rejected_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    pending_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    unit: str
    reason_code: str | None = None
    observations: str | None = None


class DeliveryQuantityValidator:
    """Helper to validate delivery quantities balance."""

    @staticmethod
    def validate_balance(line: DeliveryLineSnapshot) -> None:
        total = line.delivered_quantity + line.rejected_quantity + line.pending_quantity
        if total != line.planned_quantity:
            raise ValueError(
                f"Line {line.line_number}: Sum of delivered ({line.delivered_quantity}), "
                f"rejected ({line.rejected_quantity}) and pending ({line.pending_quantity}) "
                f"must equal planned_quantity ({line.planned_quantity})."
            )


# ---------------------------------------------------------------------------
# 3. Main Context Schemas for DELIVERY (POD, EP, RECH)
# ---------------------------------------------------------------------------

class DeliveryPodContext(BaseModel):
    """Context for POD (Prueba de Entrega)."""
    model_config = ConfigDict(extra="ignore")

    trip_reference: str
    stop_reference: str
    destination: dict[str, Any]
    occurred_at: str
    driver_snapshot: DriverSnapshot
    vehicle_snapshot: VehicleSnapshot | None = None
    receiver_snapshot: ReceiverSnapshot | None = None
    delivery_items: list[DeliveryLineSnapshot] = Field(default_factory=list)
    delivery_result: str = "DELIVERED"  # DELIVERED | DELIVERED_WITH_OBSERVATIONS | PARTIALLY_DELIVERED | REJECTED | CUSTOMER_UNAVAILABLE | RESCHEDULED | FAILED
    otp_verification: OTPVerificationSnapshot | None = None
    evidence_validation: DeliveryEvidenceValidationSnapshot | None = None
    signatures: list[dict[str, Any]] = Field(default_factory=list)
    photos: list[DeliveryPhotoEvidenceSnapshot] = Field(default_factory=list)
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_pod(self) -> DeliveryPodContext:
        if not self.delivery_items:
            raise ValueError("delivery_items must contain at least one item")
        for item in self.delivery_items:
            # If the result is completely delivered, delivered_quantity must match planned_quantity
            if self.delivery_result == "DELIVERED":
                if item.delivered_quantity != item.planned_quantity:
                    raise ValueError(f"Line {item.line_number} delivered_quantity must match planned_quantity for result DELIVERED")
            else:
                # Validate the mathematical balance
                DeliveryQuantityValidator.validate_balance(item)
        return self


class DeliveryPartialContext(BaseModel):
    """Context for EP (Acta de Entrega Parcial)."""
    model_config = ConfigDict(extra="ignore")

    delivery_attempt_reference: str
    occurred_at: str
    destination: dict[str, Any]
    items: list[DeliveryLineSnapshot] = Field(default_factory=list)
    partial_delivery_reason: str
    responsible_users: dict[str, str] = Field(default_factory=dict)
    next_action: str  # REDELIVER_SCHEDULED | RETURN_TO_WAREHOUSE | SCRAP | OTHER
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_partial(self) -> DeliveryPartialContext:
        if not self.items:
            raise ValueError("items cannot be empty")
        
        has_partial = False
        for item in self.items:
            DeliveryQuantityValidator.validate_balance(item)
            if item.rejected_quantity > 0 or item.pending_quantity > 0:
                has_partial = True

        if not has_partial:
            raise ValueError("Partial delivery document requires at least one rejected or pending item line")
            
        if not self.partial_delivery_reason.strip():
            raise ValueError("partial_delivery_reason is required")
        if not self.next_action.strip():
            raise ValueError("next_action is required")
            
        return self


class DeliveryRejectionContext(BaseModel):
    """Context for RECH (Acta de Rechazo)."""
    model_config = ConfigDict(extra="ignore")

    delivery_attempt_reference: str
    occurred_at: str
    destination: dict[str, Any]
    items: list[DeliveryLineSnapshot] = Field(default_factory=list)
    rejection_reason_code: str
    rejection_classification: str = "PRODUCT_DAMAGED"  # PRODUCT_DAMAGED | WRONG_PRODUCT | WRONG_QUANTITY | EXPIRED_PRODUCT | etc.
    packaging_status: str = "INTACT"  # INTACT | DAMAGED | DESTROYED
    evidence_references: list[str] = Field(default_factory=list)
    action_taken: str = "RETURN_TO_WAREHOUSE"
    responsible_users: dict[str, str] = Field(default_factory=dict)
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_rejection(self) -> DeliveryRejectionContext:
        if not self.items:
            raise ValueError("items cannot be empty")
        
        has_rejection = False
        for item in self.items:
            DeliveryQuantityValidator.validate_balance(item)
            if item.rejected_quantity > 0:
                has_rejection = True

        if not has_rejection:
            raise ValueError("Rejection act requires at least one rejected item line")
            
        if not self.rejection_reason_code.strip():
            raise ValueError("rejection_reason_code is required")
            
        return self


# ---------------------------------------------------------------------------
# 4. Package Manifest structures
# ---------------------------------------------------------------------------

class TransportDeliveryDocumentEntry(BaseModel):
    """Individual entry in a transport/delivery document package."""
    model_config = ConfigDict(extra="ignore")

    document_type_code: str  # HV | HR | CVT | PAR | INC | POD | EP | RECH
    family_code: str  # TRANSPORT | DELIVERY
    template_key: str
    template_version: str = "1.0.0"
    required: bool = True
    conditional: bool = False
    included: bool = True
    status: str = "PREVIEW"
    reason_if_missing: str | None = None
    render_status: str = "SUCCESS"  # SUCCESS | FAILED | SKIPPED
    sensitivity: str = "RESTRICTED"  # CONFIDENTIAL | RESTRICTED | INTERNAL
    filename_suggestion: str
    content_hash: str | None = None


class TransportDeliveryDocumentPackageManifest(BaseModel):
    """Manifest for TRANSPORT and DELIVERY document package."""
    model_config = ConfigDict(extra="ignore")

    manifest_version: str = "1.0.0"
    package_id: str | None = None
    package_mode: str  # TRIP_PLANNING | ROUTE | VEHICLE_CONTROL | STOP | INCIDENT | DELIVERY | PARTIAL_DELIVERY | REJECTED_DELIVERY | COMPLETE_TRIP_PACKAGE
    organization: str
    branch: str
    warehouse: str | None = None
    trip_reference: str
    route_plan_reference: str | None = None
    dispatch_reference: str | None = None
    vehicle_snapshot: VehicleSnapshot
    driver_snapshot: DriverSnapshot
    destination_summary: str | None = None
    document_entries: list[TransportDeliveryDocumentEntry] = Field(default_factory=list)
    external_document_references: list[dict[str, Any]] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    package_status: str = "READY_FOR_PREVIEW"  # INCOMPLETE | READY_FOR_PREVIEW | PREVIEW_GENERATED | PENDING_ROUTE | etc.
    generated_at: str
    generated_by: str
    preview_mode: bool = True
    warnings: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
