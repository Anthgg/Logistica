"""Pydantic v2 schemas for Dispatch Document contexts and Package Manifests (Phase 018).

Covers: MAN, ADSP, CPR, and OutboundDispatchDocumentPackageManifest
Phase dependencies:
  - VehicleSnapshot: PENDING_PHASE_027 / PENDING_PHASE_028
  - DriverSnapshot: PENDING_PHASE_029
  - EvidenceSnapshot: PENDING_PHASE_030
  - SealHistory: PENDING_PHASE_058
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.logistics.documents.rendering.outbound_schemas import (
    DestinationSnapshot,
    PackingUnit,
    Weight,
    Volume,
)


# ---------------------------------------------------------------------------
# 1. Snapshots for Dispatch & Transportation
# ---------------------------------------------------------------------------


class VehicleSnapshot(BaseModel):
    """Vehicle details snapshot (PENDING_PHASE_027 / PENDING_PHASE_028)."""

    model_config = ConfigDict(extra="ignore")

    vehicle_id: str | None = None
    plate: str
    vehicle_type: str = "TRUCK"  # TRUCK | VAN | MOTORCYCLE | CAR | OTHER
    capacity_weight: Decimal | None = Field(default=None, ge=0)  # in kg
    capacity_volume: Decimal | None = Field(default=None, ge=0)  # in m3
    verification_state: str = "PENDING"  # PENDING | VERIFIED | FAILED


class DriverSnapshot(BaseModel):
    """Driver details snapshot (PENDING_PHASE_029)."""

    model_config = ConfigDict(extra="ignore")

    driver_id: str | None = None
    full_name: str
    document_number: str  # Masked in service/schema
    license_number: str   # Masked in service/schema
    license_category: str | None = None
    verification_state: str = "PENDING"  # PENDING | VERIFIED | FAILED


class SealEventSnapshot(BaseModel):
    """Snapshot of a seal integrity event (PENDING_PHASE_058)."""

    model_config = ConfigDict(extra="ignore")

    event_type: str  # APPLIED | VERIFIED | BROKEN | REMOVED | REPLACED | MISMATCH_DETECTED | MISSING_DETECTED
    seal_number: str
    previous_seal_number: str | None = None
    status: str = "PENDING"  # PENDING | MATCHED | MISMATCHED | BROKEN | MISSING | REPLACED | VERIFIED | CANCELLED
    occurred_at: str
    actor: str
    reason: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    verification_state: str = "PENDING"


# ---------------------------------------------------------------------------
# 2. Capacity and Load Validators
# ---------------------------------------------------------------------------


class VehicleCapacityValidationResult(BaseModel):
    """Capacity validation results for Load Manifests."""

    model_config = ConfigDict(extra="ignore")

    capacity_weight: Decimal | None = None
    capacity_volume: Decimal | None = None
    planned_weight: Decimal = Decimal("0.00")
    planned_volume: Decimal = Decimal("0.00")
    weight_utilization_percentage: Decimal | None = None
    volume_utilization_percentage: Decimal | None = None
    overweight: bool = False
    overvolume: bool = False
    validation_status: str = "NOT_EVALUATED"  # NOT_EVALUATED | WITHIN_LIMIT | NEAR_LIMIT | EXCEEDED | DATA_INCOMPLETE
    warnings: list[str] = Field(default_factory=list)


class CapacityCalculator:
    """Helper to calculate vehicle capacity utilization."""

    @staticmethod
    def evaluate(
        planned_w: Decimal, planned_v: Decimal, vehicle: VehicleSnapshot | None
    ) -> VehicleCapacityValidationResult:
        res = VehicleCapacityValidationResult(planned_weight=planned_w, planned_volume=planned_v)
        if not vehicle:
            res.validation_status = "DATA_INCOMPLETE"
            res.warnings.append("Vehicle information missing. Capacity cannot be evaluated.")
            return res

        res.capacity_weight = vehicle.capacity_weight
        res.capacity_volume = vehicle.capacity_volume

        warnings = []
        status = "WITHIN_LIMIT"

        # Evaluate weight
        if vehicle.capacity_weight and vehicle.capacity_weight > 0:
            w_pct = (planned_w / vehicle.capacity_weight) * Decimal("100.0")
            res.weight_utilization_percentage = w_pct.quantize(Decimal("0.1"))
            if planned_w > vehicle.capacity_weight:
                res.overweight = True
                status = "EXCEEDED"
                warnings.append(f"Capacity weight exceeded! Planned: {planned_w} kg, Capacity: {vehicle.capacity_weight} kg")
            elif w_pct >= 90:
                status = "NEAR_LIMIT"
                warnings.append("Capacity weight is near limit (>90%)")
        else:
            warnings.append("Vehicle weight capacity not defined.")

        # Evaluate volume
        if vehicle.capacity_volume and vehicle.capacity_volume > 0:
            v_pct = (planned_v / vehicle.capacity_volume) * Decimal("100.0")
            res.volume_utilization_percentage = v_pct.quantize(Decimal("0.1"))
            if planned_v > vehicle.capacity_volume:
                res.overvolume = True
                status = "EXCEEDED"
                warnings.append(f"Capacity volume exceeded! Planned: {planned_v} m3, Capacity: {vehicle.capacity_volume} m3")
            elif v_pct >= 90:
                if status != "EXCEEDED":
                    status = "NEAR_LIMIT"
                warnings.append("Capacity volume is near limit (>90%)")
        else:
            warnings.append("Vehicle volume capacity not defined.")

        res.validation_status = status
        res.warnings = warnings
        return res


# ---------------------------------------------------------------------------
# 3. Context schemas for MAN, ADSP, CPR
# ---------------------------------------------------------------------------


class DispatchManContext(BaseModel):
    """Context schema for MAN (Manifiesto de Carga)."""

    model_config = ConfigDict(extra="ignore")

    dispatch_reference: str
    warehouse: str
    planned_departure_at: str | None = None
    vehicle_snapshot: VehicleSnapshot
    driver_snapshot: DriverSnapshot
    packing_units: list[PackingUnit] = Field(default_factory=list)
    responsible_users: list[str] = Field(default_factory=list)
    status: str = "PREVIEW"
    dock: str | None = None
    carrier_name: str | None = None
    destination_summary: str | None = None
    external_document_references: list[dict[str, Any]] = Field(default_factory=list)
    observations: str | None = None
    capacity_validation: VehicleCapacityValidationResult | None = None

    @model_validator(mode="after")
    def validate_man_basics(self) -> DispatchManContext:
        if not self.packing_units:
            raise ValueError("MAN requires at least one packing unit")
        if not self.vehicle_snapshot:
            raise ValueError("MAN requires a vehicle")
        if not self.driver_snapshot:
            raise ValueError("MAN requires a driver")

        # Run capacity validation automatically if not provided
        if not self.capacity_validation:
            planned_w = sum((u.gross_weight.value if u.gross_weight else Decimal("0.00")) for u in self.packing_units)
            # Volume sum
            planned_v = sum((u.volume.value if u.volume else Decimal("0.00")) for u in self.packing_units)
            self.capacity_validation = CapacityCalculator.evaluate(planned_w, planned_v, self.vehicle_snapshot)

        return self


class DispatchAdspContext(BaseModel):
    """Context schema for ADSP (Acta de Despacho)."""

    model_config = ConfigDict(extra="ignore")

    dispatch_reference: str
    manifest_reference: str
    warehouse: str
    vehicle_snapshot: VehicleSnapshot
    driver_snapshot: DriverSnapshot
    loading_start: str
    loading_end: str
    expected_units: int = Field(..., ge=0)
    loaded_units: int = Field(..., ge=0)
    result: str = "PREVIEW"  # LOADED_WITHOUT_DIFFERENCES | LOADED_WITH_OBSERVATIONS | PARTIALLY_LOADED | DIFFERENCE_DETECTED | REJECTED | PENDING_REVIEW | PREVIEW
    responsible_users: list[str] = Field(default_factory=list)
    dock: str | None = None
    carrier_name: str | None = None
    planned_weight: Decimal = Decimal("0.00")
    loaded_weight: Decimal = Decimal("0.00")
    seal_number: str | None = None
    differences_summary: str | None = None
    observations: str | None = None

    @model_validator(mode="after")
    def validate_adsp_basics(self) -> DispatchAdspContext:
        # Check start/end time coherence if possible (just string comparison for basic validation)
        if self.loading_start and self.loading_end:
            if self.loading_end < self.loading_start:
                raise ValueError("loading_end cannot be before loading_start")
        if self.loaded_units < 0:
            raise ValueError("loaded_units cannot be negative")
        return self


class DispatchCprContext(BaseModel):
    """Context schema for CPR (Control de Precinto). Proposed code."""

    model_config = ConfigDict(extra="ignore")

    dispatch_reference: str
    vehicle_snapshot: VehicleSnapshot
    observed_seal_number: str
    seal_status: str = "PENDING"  # PENDING | MATCHED | MISMATCHED | BROKEN | MISSING | REPLACED | VERIFIED | CANCELLED
    applied_at: str | None = None
    applied_by: str | None = None
    verified_by: str | None = None
    expected_seal_number: str | None = None
    gate_code: str | None = None
    reason_if_replaced_or_broken: str | None = None
    seal_events: list[SealEventSnapshot] = Field(default_factory=list)
    observations: str | None = None

    @model_validator(mode="after")
    def validate_cpr_basics(self) -> DispatchCprContext:
        if not self.observed_seal_number:
            raise ValueError("observed_seal_number cannot be empty")
        
        # Enforce reason if mismatched or broken
        if self.seal_status in ("MISMATCHED", "BROKEN", "REPLACED") and not self.reason_if_replaced_or_broken:
            raise ValueError(f"reason_if_replaced_or_broken is required when seal_status is {self.seal_status}")
            
        return self


# ---------------------------------------------------------------------------
# 4. Document Package Manifest Schema
# ---------------------------------------------------------------------------


class OutboundDispatchDocumentEntry(BaseModel):
    """Single document entry within an outbound/dispatch package manifest."""

    model_config = ConfigDict(extra="ignore")

    document_type_code: str
    template_key: str
    template_version: str = "1.0.0"
    required: bool = True
    included: bool = True
    status: str = "READY_FOR_PREVIEW"
    reason_if_missing: str | None = None
    render_status: str = "PENDING"
    filename_suggestion: str | None = None
    content_hash: str | None = None


class OutboundDispatchDocumentPackageManifest(BaseModel):
    """Manifest for an outbound/dispatch document package."""

    model_config = ConfigDict(extra="ignore")

    manifest_version: str = "1.0.0"
    package_mode: str  # OUTBOUND_REQUEST | OUTBOUND_AUTHORIZATION | PICKING | PACKING | DISPATCH | TRANSPORT_HANDOFF
    package_status: str = "READY_FOR_PREVIEW"
    organization_name: str = "PROYECTO T1 LOGÍSTICA S.A.C."
    branch_name: str = "SEDE LIMA PRINCIPAL"
    warehouse: str
    destination: DestinationSnapshot | None = None
    outbound_request_reference: str | None = None
    outbound_order_reference: str | None = None
    picking_reference: str | None = None
    packing_reference: str | None = None
    dispatch_reference: str | None = None
    manifest_reference: str | None = None
    trip_reference: str | None = None
    document_entries: list[OutboundDispatchDocumentEntry] = Field(default_factory=list)
    external_document_references: list[dict[str, Any]] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    preview_mode: bool = True
    warnings: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
