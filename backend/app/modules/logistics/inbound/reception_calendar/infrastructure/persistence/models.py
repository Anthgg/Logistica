"""SQLAlchemy models for warehouse reception scheduling (Phase 036)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.database.base import Base

_WEIGHT = dict(precision=28, scale=10)


class WarehouseReceptionCalendarModel(Base):
    __tablename__ = "warehouse_reception_calendars"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("slot_duration_minutes > 0", name="ck_reception_calendar_slot_duration"),
        CheckConstraint("booking_horizon_days >= 0", name="ck_reception_calendar_horizon"),
        CheckConstraint("minimum_advance_minutes >= 0", name="ck_reception_calendar_min_advance"),
        CheckConstraint("maximum_advance_days >= 0", name="ck_reception_calendar_max_advance"),
        CheckConstraint(
            "default_max_concurrent_appointments > 0",
            name="ck_reception_calendar_max_concurrent",
        ),
        Index("ix_reception_calendars_org", "organization_id"),
        Index("ix_reception_calendars_warehouse", "warehouse_id"),
        Index("ix_reception_calendars_status", "status"),
        Index(
            "uq_reception_calendar_active_warehouse",
            "warehouse_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name = Column(String(160), nullable=False)
    timezone = Column(String(64), nullable=False)
    slot_duration_minutes = Column(Integer, nullable=False, default=60)
    booking_horizon_days = Column(Integer, nullable=False, default=90)
    minimum_advance_minutes = Column(Integer, nullable=False, default=120)
    maximum_advance_days = Column(Integer, nullable=False, default=90)
    cancellation_cutoff_minutes = Column(Integer, nullable=False, default=120)
    reschedule_cutoff_minutes = Column(Integer, nullable=False, default=240)
    hold_duration_minutes = Column(Integer, nullable=False, default=10)
    maximum_hold_refreshes = Column(Integer, nullable=False, default=1)
    default_max_concurrent_appointments = Column(Integer, nullable=False, default=1)
    default_max_pallets_per_slot = Column(Integer, nullable=True)
    default_max_packages_per_slot = Column(Integer, nullable=True)
    default_max_weight_per_slot = Column(Numeric(**_WEIGHT), nullable=True)
    weight_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status = Column(String(20), nullable=False, default="DRAFT")
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, default=1)


class WarehouseReceptionOperatingWindowModel(Base):
    __tablename__ = "warehouse_reception_operating_windows"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_reception_window_weekday"),
        CheckConstraint("start_local_time < end_local_time", name="ck_reception_window_time_order"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_reception_window_effective_dates",
        ),
        CheckConstraint(
            "max_concurrent_appointments IS NULL OR max_concurrent_appointments > 0",
            name="ck_reception_window_concurrent",
        ),
        Index("ix_reception_windows_calendar_day", "calendar_id", "day_of_week"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    calendar_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_reception_calendars.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week = Column(Integer, nullable=False)
    start_local_time = Column(Time, nullable=False)
    end_local_time = Column(Time, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    max_concurrent_appointments = Column(Integer, nullable=True)
    max_pallets = Column(Integer, nullable=True)
    max_packages = Column(Integer, nullable=True)
    max_weight = Column(Numeric(**_WEIGHT), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WarehouseReceptionBlackoutModel(Base):
    __tablename__ = "warehouse_reception_blackouts"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("starts_at < ends_at", name="ck_reception_blackout_time_order"),
        Index("ix_reception_blackouts_calendar", "calendar_id"),
        Index("ix_reception_blackouts_range", "starts_at", "ends_at"),
        Index("ix_reception_blackouts_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    calendar_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_reception_calendars.id", ondelete="CASCADE"),
        nullable=False,
    )
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    reason_code = Column(String(40), nullable=False)
    reason = Column(Text, nullable=False)
    affects_all_appointments = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionAppointmentHoldModel(Base):
    __tablename__ = "reception_appointment_holds"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("slot_start < slot_end", name="ck_reception_hold_slot_order"),
        CheckConstraint("expected_pallet_count >= 0", name="ck_reception_hold_pallets"),
        CheckConstraint("expected_package_count >= 0", name="ck_reception_hold_packages"),
        CheckConstraint("expected_weight >= 0", name="ck_reception_hold_weight"),
        Index("ix_reception_holds_warehouse", "warehouse_id"),
        Index("ix_reception_holds_slot", "slot_start", "slot_end"),
        Index("ix_reception_holds_expires", "expires_at"),
        Index("ix_reception_holds_status", "status"),
        Index(
            "uq_reception_hold_active_notice",
            "arrival_notice_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calendar_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_reception_calendars.id", ondelete="RESTRICT"),
        nullable=False,
    )
    arrival_notice_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slot_start = Column(DateTime(timezone=True), nullable=False)
    slot_end = Column(DateTime(timezone=True), nullable=False)
    expected_pallet_count = Column(Integer, nullable=False, default=0)
    expected_package_count = Column(Integer, nullable=False, default=0)
    expected_weight = Column(Numeric(**_WEIGHT), nullable=False, default=0)
    weight_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, default="ACTIVE")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_count = Column(Integer, nullable=False, default=0)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionAppointmentModel(Base):
    __tablename__ = "reception_appointments"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "normalized_appointment_code",
            name="uq_reception_appointment_org_code",
        ),
        CheckConstraint("slot_start < slot_end", name="ck_reception_appointment_slot_order"),
        CheckConstraint("expected_pallet_count >= 0", name="ck_reception_appointment_pallets"),
        CheckConstraint("expected_package_count >= 0", name="ck_reception_appointment_packages"),
        CheckConstraint("expected_gross_weight >= 0", name="ck_reception_appointment_weight"),
        CheckConstraint("row_version >= 1", name="ck_reception_appointment_row_version"),
        Index("ix_reception_appointments_org", "organization_id"),
        Index("ix_reception_appointments_warehouse", "warehouse_id"),
        Index("ix_reception_appointments_slot", "slot_start", "slot_end"),
        Index("ix_reception_appointments_status", "status"),
        Index("ix_reception_appointments_code", "normalized_appointment_code"),
        Index("ix_reception_appointments_notice", "arrival_notice_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calendar_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_reception_calendars.id", ondelete="RESTRICT"),
        nullable=False,
    )
    arrival_notice_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    arrival_notice_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appointment_code = Column(String(80), nullable=True)
    normalized_appointment_code = Column(String(80), nullable=True)
    document_instance_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_instances.id", ondelete="RESTRICT"),
        nullable=True,
    )
    document_series_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_series.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status = Column(String(40), nullable=False, default="PROPOSED")
    slot_start = Column(DateTime(timezone=True), nullable=False)
    slot_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False)
    expected_pallet_count = Column(Integer, nullable=False, default=0)
    expected_package_count = Column(Integer, nullable=False, default=0)
    expected_gross_weight = Column(Numeric(**_WEIGHT), nullable=False, default=0)
    weight_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_reference_snapshot = Column(JSONB, nullable=True)
    driver_reference_snapshot = Column(JSONB, nullable=True)
    supplier_snapshot = Column(JSONB, nullable=False, default=dict)
    carrier_snapshot = Column(JSONB, nullable=True)
    contact_snapshot = Column(JSONB, nullable=True)
    special_requirements_snapshot = Column(JSONB, nullable=False, default=list)
    confirmation_notes = Column(Text, nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    rescheduled_from_appointment_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("reception_appointments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reschedule_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(PG_UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    window_elapsed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, default=1)


class ReceptionAppointmentHistoryModel(Base):
    __tablename__ = "reception_appointment_history"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_reception_appointment_history_appointment", "appointment_id", "created_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    appointment_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("reception_appointments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type = Column(String(80), nullable=False)
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=True)
    previous_slot = Column(JSONB, nullable=True)
    new_slot = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    actor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    metadata_data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionAppointmentPackageJobModel(Base):
    __tablename__ = "reception_appointment_package_jobs"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_reception_package_job_idempotency",
        ),
        Index("ix_reception_package_jobs_status", "status", "available_at"),
        Index("ix_reception_package_jobs_appointment", "appointment_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appointment_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("reception_appointments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    idempotency_key = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    file_asset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_assets.id", ondelete="RESTRICT"),
        nullable=True,
    )
    artifact_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_artifacts.id", ondelete="RESTRICT"),
        nullable=True,
    )
    manifest = Column(JSONB, nullable=False, default=dict)
    attempt_count = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
