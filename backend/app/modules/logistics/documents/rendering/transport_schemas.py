"""Pydantic v2 schemas for Transport Document contexts (Phase 019).

Covers: HV, HR, CVT, PAR, INC
Phase boundaries:
  - Vehicle pre-operational checklist (CVT)
  - Stops timeline and GPS validation (PAR)
  - Incident reports and severity validations (INC)
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.logistics.documents.rendering.dispatch_schemas import (
    VehicleSnapshot,
    DriverSnapshot,
)


# ---------------------------------------------------------------------------
# 1. Base Transport Snapshots
# ---------------------------------------------------------------------------

class CoordinatesSnapshot(BaseModel):
    """Coordinates details with validation rules (PENDING_PHASE_064)."""
    model_config = ConfigDict(extra="ignore")

    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    accuracy_meters: Decimal | None = Field(default=None, ge=0)
    captured_at: str | None = None
    source: str = "DEVICE_GPS"  # ROUTE_PROVIDER | DEVICE_GPS | GEOCODER | MANUAL_CONFIRMED | GEOFENCE_EVENT | DEMO
    verification_state: str = "PENDING"  # PENDING | VERIFIED | FAILED
    is_demo_data: bool = False


class RouteStopSnapshot(BaseModel):
    """Route stop details (PENDING_PHASE_064)."""
    model_config = ConfigDict(extra="ignore")

    stop_id: str | None = None
    sequence: int = Field(..., ge=1)
    stop_type: str = "DELIVERY"  # ORIGIN | DELIVERY | PICKUP | CHECKPOINT | FUEL | TOLL | REST | WAREHOUSE | RETURN | OTHER
    name: str
    address: str
    coordinates: CoordinatesSnapshot | None = None
    planned_arrival_at: str | None = None
    planned_departure_at: str | None = None
    service_duration_seconds: int | None = Field(default=None, ge=0)
    delivery_window_start: str | None = None
    delivery_window_end: str | None = None
    contact: str | None = None
    instructions: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING | ARRIVED | COMPLETED | FAILED | SKIPPED
    is_demo_data: bool = False


class RoutePlanSnapshot(BaseModel):
    """Calculated Route Plan Snapshot (PENDING_PHASE_061 / 062)."""
    model_config = ConfigDict(extra="ignore")

    route_plan_id: str | None = None
    route_version: str = "1.0.0"
    provider: str = "DEMO"  # OSRM | ORS | MAPBOX | GOOGLE | DEMO
    provider_request_id: str | None = None
    calculated_at: str | None = None
    valid_until: str | None = None
    calculation_status: str = "DEMO_ONLY"  # NOT_CALCULATED | PENDING | CALCULATED | EXPIRED | INVALID | FAILED | DEMO_ONLY
    origin: str
    destination: str
    stops: list[RouteStopSnapshot] = Field(default_factory=list)
    total_distance_meters: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_duration_seconds: int = Field(default=0, ge=0)
    geometry_reference: str | None = None
    geometry_hash: str | None = None
    instructions: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    vehicle_profile: str = "DEFAULT"
    traffic_considered: bool = False
    tolls_considered: bool = False
    source_status: str = "ACTIVE"
    is_demo_data: bool = True

    @model_validator(mode="after")
    def validate_route_rules(self) -> RoutePlanSnapshot:
        # Rule against fake routes: calculated_at is required if status is CALCULATED
        if self.calculation_status == "CALCULATED":
            if not self.calculated_at:
                raise ValueError("calculated_at is required for CALCULATED routes")
            if not self.geometry_reference:
                raise ValueError("geometry_reference is required for CALCULATED routes")
        return self


# ---------------------------------------------------------------------------
# 2. Checklist items for CVT
# ---------------------------------------------------------------------------

class VehicleChecklistItem(BaseModel):
    """Checklist item for pre-operational inspections."""
    model_config = ConfigDict(extra="ignore")

    code: str
    category: str  # DOCUMENTATION | SAFETY | MECHANICAL | BODY | CARGO_AREA | COLD_CHAIN | EMERGENCY | OTHER
    label: str
    required: bool = True
    result: str = "NOT_CHECKED"  # PASS | FAIL | OBSERVED | NOT_APPLICABLE | NOT_CHECKED
    observation: str | None = None
    evidence_required: bool = False
    evidence_references: list[str] = Field(default_factory=list)
    severity_if_failed: str = "MINOR"  # MINOR | MAJOR | CRITICAL


# ---------------------------------------------------------------------------
# 3. Main Context Schemas for TRANSPORT (HV, HR, CVT, PAR, INC)
# ---------------------------------------------------------------------------

class OutboundTripContext(BaseModel):
    """Context for HV (Hoja de viaje)."""
    model_config = ConfigDict(extra="ignore")

    trip_reference: str
    trip_date: str
    dispatch_reference: str | None = None
    vehicle_snapshot: VehicleSnapshot
    driver_snapshot: DriverSnapshot
    carrier_snapshot: dict[str, Any] = Field(default_factory=dict)
    origin: str
    destination_final: str
    planned_stops: list[RouteStopSnapshot] = Field(default_factory=list)
    planned_departure_at: str
    planned_return_at: str | None = None
    responsible_users: dict[str, str] = Field(default_factory=dict)
    load_summary: dict[str, Any] = Field(default_factory=dict)
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_stops(self) -> OutboundTripContext:
        if not self.planned_stops:
            raise ValueError("planned_stops must contain at least one stop")
        return self


class OutboundRouteContext(BaseModel):
    """Context for HR (Hoja de ruta)."""
    model_config = ConfigDict(extra="ignore")

    route_plan_reference: str
    route_version: str = "1.0.0"
    provider: str
    calculated_at: str | None = None
    origin: str
    destination: str
    stops: list[RouteStopSnapshot] = Field(default_factory=list)
    total_distance_meters: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_duration_seconds: int = Field(default=0, ge=0)
    calculation_status: str = "CALCULATED"
    instructions: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    vehicle_profile: str = "DEFAULT"
    is_demo_data: bool = False
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_itinerary(self) -> OutboundRouteContext:
        if not self.stops:
            raise ValueError("stops list cannot be empty")
        
        # Check unique sequence orders
        sequences = [s.sequence for s in self.stops]
        if len(sequences) != len(set(sequences)):
            raise ValueError("Stops sequences must be unique and non-duplicated")
            
        return self


class VehicleControlContext(BaseModel):
    """Context for CVT (Control Vehicular de Transporte - Proposed)."""
    model_config = ConfigDict(extra="ignore")

    trip_reference: str
    vehicle_snapshot: VehicleSnapshot
    driver_snapshot: DriverSnapshot
    inspected_at: str
    inspected_by: str
    odometer: Decimal | None = Field(default=None, ge=0)
    fuel_level: str | None = None  # Empty | Quarter | Half | ThreeQuarters | Full
    checklist: list[VehicleChecklistItem] = Field(default_factory=list)
    verification_state: str = "FIT_FOR_OPERATION"  # FIT_FOR_OPERATION | FIT_WITH_OBSERVATIONS | NOT_FIT | PENDING_REVIEW
    notes: str | None = None
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_safety_rules(self) -> VehicleControlContext:
        # Check if any checklist item fails with CRITICAL severity
        critical_failed = any(
            item.result == "FAIL" and item.severity_if_failed == "CRITICAL"
            for item in self.checklist
        )
        if critical_failed and self.verification_state != "NOT_FIT":
            raise ValueError("Verification state must be NOT_FIT if a critical safety item has failed")
        return self


class StopRecordContext(BaseModel):
    """Context for PAR (Constancia de Parada - Proposed)."""
    model_config = ConfigDict(extra="ignore")

    trip_reference: str
    route_stop_reference: str
    sequence: int = Field(..., ge=1)
    stop_type: str = "DELIVERY"
    address: str
    coordinates: CoordinatesSnapshot | None = None
    planned_arrival_at: str
    real_arrival_at: str | None = None
    real_departure_at: str | None = None
    waiting_seconds: int | None = Field(default=None, ge=0)
    service_seconds: int | None = Field(default=None, ge=0)
    result: str = "ARRIVED"  # ARRIVED | COMPLETED | PARTIALLY_COMPLETED | FAILED | SKIPPED
    reason_if_failed_or_skipped: str | None = None
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_failure_reason(self) -> StopRecordContext:
        if self.result in ("FAILED", "SKIPPED") and not self.reason_if_failed_or_skipped:
            raise ValueError("reason_if_failed_or_skipped is required for FAILED or SKIPPED results")
        return self


class IncidentReportContext(BaseModel):
    """Context for INC (Reporte de incidencia)."""
    model_config = ConfigDict(extra="ignore")

    incident_code: str
    trip_reference: str
    route_stop_reference: str | None = None
    occurred_at: str
    incident_type: str  # DELAY | DAMAGE | THEFT | LOSS | TEMPERATURE | ACCIDENT | etc.
    severity: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    description: str
    affected_items: list[dict[str, Any]] = Field(default_factory=list)
    immediate_action: str | None = None
    reported_by: str
    evidence_references: list[str] = Field(default_factory=list)
    preview_mode: bool = True

    @model_validator(mode="after")
    def validate_incident_severity(self) -> IncidentReportContext:
        if not self.description.strip():
            raise ValueError("description cannot be empty")
        if self.severity in ("HIGH", "CRITICAL") and not self.immediate_action:
            raise ValueError("immediate_action is required for HIGH or CRITICAL incidents")
        return self
