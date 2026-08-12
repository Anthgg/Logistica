"""Pydantic v2 contracts for reception calendars, holds and appointments."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from app.modules.logistics.inbound.arrival_notices.presentation.schemas.schemas import (
    ApiModel,
    DecimalString,
)
from app.modules.logistics.inbound.reception_calendar.domain.enums import BlackoutReason


class ReceptionCalendarCreate(ApiModel):
    warehouse_id: UUID
    name: str = Field(min_length=3, max_length=160)
    timezone: str = Field(min_length=1, max_length=64)
    slot_duration_minutes: int = Field(default=60, ge=5, le=720)
    booking_horizon_days: int = Field(default=90, ge=1, le=730)
    minimum_advance_minutes: int = Field(default=120, ge=0)
    maximum_advance_days: int = Field(default=90, ge=1, le=730)
    cancellation_cutoff_minutes: int = Field(default=120, ge=0)
    reschedule_cutoff_minutes: int = Field(default=240, ge=0)
    hold_duration_minutes: int = Field(default=10, ge=5, le=15)
    maximum_hold_refreshes: int = Field(default=1, ge=0, le=3)
    default_max_concurrent_appointments: int = Field(default=1, ge=1)
    default_max_pallets_per_slot: int | None = Field(default=None, ge=0)
    default_max_packages_per_slot: int | None = Field(default=None, ge=0)
    default_max_weight_per_slot: DecimalString | None = Field(default=None, ge=Decimal("0"))
    weight_unit_id: UUID | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Zona horaria IANA inválida.") from exc
        return value


class ReceptionCalendarUpdate(ApiModel):
    row_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=3, max_length=160)
    timezone: str | None = Field(default=None, max_length=64)
    slot_duration_minutes: int | None = Field(default=None, ge=5, le=720)
    booking_horizon_days: int | None = Field(default=None, ge=1, le=730)
    minimum_advance_minutes: int | None = Field(default=None, ge=0)
    maximum_advance_days: int | None = Field(default=None, ge=1, le=730)
    cancellation_cutoff_minutes: int | None = Field(default=None, ge=0)
    reschedule_cutoff_minutes: int | None = Field(default=None, ge=0)
    hold_duration_minutes: int | None = Field(default=None, ge=5, le=15)
    maximum_hold_refreshes: int | None = Field(default=None, ge=0, le=3)
    default_max_concurrent_appointments: int | None = Field(default=None, ge=1)
    default_max_pallets_per_slot: int | None = Field(default=None, ge=0)
    default_max_packages_per_slot: int | None = Field(default=None, ge=0)
    default_max_weight_per_slot: DecimalString | None = Field(default=None, ge=Decimal("0"))
    weight_unit_id: UUID | None = None


class ReceptionCalendarResponse(ApiModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    name: str
    timezone: str
    slot_duration_minutes: int
    booking_horizon_days: int
    minimum_advance_minutes: int
    maximum_advance_days: int
    cancellation_cutoff_minutes: int
    reschedule_cutoff_minutes: int
    hold_duration_minutes: int
    maximum_hold_refreshes: int
    default_max_concurrent_appointments: int
    default_max_pallets_per_slot: int | None
    default_max_packages_per_slot: int | None
    default_max_weight_per_slot: Decimal | None
    weight_unit_id: UUID | None
    status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


class ReceptionOperatingWindowCreate(ApiModel):
    day_of_week: int = Field(ge=0, le=6)
    start_local_time: time
    end_local_time: time
    effective_from: date
    effective_to: date | None = None
    max_concurrent_appointments: int | None = Field(default=None, ge=1)
    max_pallets: int | None = Field(default=None, ge=0)
    max_packages: int | None = Field(default=None, ge=0)
    max_weight: DecimalString | None = Field(default=None, ge=Decimal("0"))

    @model_validator(mode="after")
    def validate_window(self):
        if self.start_local_time >= self.end_local_time:
            raise ValueError("La hora inicial debe ser anterior a la hora final.")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("La vigencia final no puede ser anterior a la inicial.")
        return self


class ReceptionOperatingWindowResponse(ApiModel):
    id: UUID
    calendar_id: UUID
    day_of_week: int
    start_local_time: time
    end_local_time: time
    effective_from: date
    effective_to: date | None
    max_concurrent_appointments: int | None
    max_pallets: int | None
    max_packages: int | None
    max_weight: Decimal | None
    status: str


class ReceptionBlackoutCreate(ApiModel):
    starts_at: datetime
    ends_at: datetime
    reason_code: BlackoutReason
    reason: str = Field(min_length=10, max_length=2000)
    affects_all_appointments: bool = True

    @model_validator(mode="after")
    def validate_range(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Los blackouts requieren timestamps con zona horaria.")
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at debe ser anterior a ends_at.")
        return self


class ReceptionBlackoutResponse(ApiModel):
    id: UUID
    calendar_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason_code: str
    reason: str
    affects_all_appointments: bool
    status: str


class ReceptionAvailabilityRequest(ApiModel):
    starts_on: date
    ends_on: date
    timezone: str
    expected_pallet_count: int = Field(default=0, ge=0)
    expected_package_count: int = Field(default=0, ge=0)
    expected_weight: DecimalString = Field(default=Decimal("0"), ge=Decimal("0"))
    weight_unit_id: UUID
    transport_mode: str | None = Field(default=None, max_length=50)
    special_requirements: list[str] = Field(default_factory=list, max_length=20)
    desired_duration_minutes: int | None = Field(default=None, ge=5, le=720)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_on < self.starts_on:
            raise ValueError("ends_on no puede ser anterior a starts_on.")
        if (self.ends_on - self.starts_on).days > 90:
            raise ValueError("La consulta de disponibilidad no puede exceder 90 días.")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Zona horaria IANA inválida.") from exc
        return self


class ReceptionAvailabilitySlot(ApiModel):
    slot_start: datetime
    slot_end: datetime
    timezone: str
    availability_status: str
    remaining_appointments: int
    remaining_pallet_capacity: int | None
    remaining_package_capacity: int | None
    remaining_weight_capacity: Decimal | None
    warnings: list[str] = Field(default_factory=list)
    hold_supported: bool = True


class ReceptionAvailabilityResponse(ApiModel):
    slots: list[ReceptionAvailabilitySlot]
    server_time: datetime
    availability_version: str


class ReceptionAppointmentHoldCreate(ApiModel):
    arrival_notice_id: UUID
    calendar_id: UUID
    slot_start: datetime
    slot_end: datetime
    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_slot(self):
        if self.slot_start.tzinfo is None or self.slot_end.tzinfo is None:
            raise ValueError("La franja requiere timestamps con zona horaria.")
        if self.slot_start >= self.slot_end:
            raise ValueError("slot_start debe ser anterior a slot_end.")
        return self


class ReceptionAppointmentHoldResponse(ApiModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    calendar_id: UUID
    arrival_notice_id: UUID
    slot_start: datetime
    slot_end: datetime
    expected_pallet_count: int
    expected_package_count: int
    expected_weight: Decimal
    weight_unit_id: UUID
    status: str
    expires_at: datetime
    refresh_count: int


class ReceptionAppointmentCreate(ApiModel):
    arrival_notice_id: UUID
    hold_id: UUID
    contact_snapshot: dict | None = None
    confirmation_notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ReceptionAppointmentConfirmRequest(ApiModel):
    hold_id: UUID | None = None
    confirmation_notes: str | None = Field(default=None, max_length=2000)
    capacity_override_reason: str | None = Field(default=None, min_length=10, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ReceptionAppointmentRescheduleRequest(ApiModel):
    hold_id: UUID
    reason: str = Field(min_length=10, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ReceptionAppointmentCancelRequest(ApiModel):
    reason: str = Field(min_length=10, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ReceptionAppointmentResponse(ApiModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    calendar_id: UUID
    arrival_notice_id: UUID
    arrival_notice_revision_id: UUID
    appointment_code: str | None
    document_instance_id: UUID | None
    status: str
    slot_start: datetime
    slot_end: datetime
    timezone: str
    expected_pallet_count: int
    expected_package_count: int
    expected_gross_weight: Decimal
    weight_unit_id: UUID
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    row_version: int
    created_at: datetime
    updated_at: datetime


class ReceptionAppointmentValidationResponse(ApiModel):
    valid: bool
    capacity_status: str
    transport_status: str
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)


class GateCheckInPreparationResponse(ApiModel):
    appointment_id: UUID
    appointment_code: str | None
    arrival_notice_id: UUID
    warehouse_id: UUID
    expected_slot: dict
    supplier: dict
    carrier: dict | None
    expected_plate: str | None
    expected_vehicle_id: UUID | None
    expected_driver_id: UUID | None
    guide_references: list[str]
    expected_seal_reference: str | None = None
    documents_summary: list[dict]
    special_requirements: list[str]
    verification_warnings: list[str]
    appointment_status: str
    check_in_capabilities_future: list[str] = Field(default_factory=list)


class ReceptionAppointmentPackageRequest(ApiModel):
    include_supplier_visible_files: bool = True
    idempotency_key: str = Field(min_length=8, max_length=128)


class ReceptionAppointmentPackageResponse(ApiModel):
    id: UUID
    appointment_id: UUID
    status: str
    manifest: dict
    file_asset_id: UUID | None
    artifact_id: UUID | None
