"""SQLAlchemy 2 persistence model for Phase 038 dock operations.

The model intentionally has no received, accepted, rejected, lot, serial,
pallet, stock, or inventory movement fields.
"""

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


_ACTIVE_QUEUE_SQL = "queue_status IN ('WAITING','READY','ASSIGNED','ON_HOLD')"
_ACTIVE_ASSIGNMENT_SQL = (
    "status IN ('ASSIGNED','MOVING_TO_DOCK','AT_DOCK','READY_FOR_UNLOADING',"
    "'UNLOADING_IN_PROGRESS','UNLOADING_PAUSED','UNLOADING_COMPLETED',"
    "'RELEASE_PENDING','REASSIGNMENT_REQUIRED')"
)
_ACTIVE_OPERATION_SQL = "status IN ('CREATED','READINESS_PENDING','READY','IN_PROGRESS','PAUSED')"


class WarehouseDockModel(Base):
    __tablename__ = "warehouse_docks"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "normalized_code", name="uq_warehouse_dock_code"),
        CheckConstraint("simultaneous_vehicle_capacity >= 1", name="ck_dock_vehicle_capacity"),
        CheckConstraint("row_version >= 1", name="ck_dock_row_version"),
        Index("ix_warehouse_docks_org", "organization_id"),
        Index("ix_warehouse_docks_warehouse", "warehouse_id"),
        Index("ix_warehouse_docks_status", "status"),
        Index("ix_warehouse_docks_direction", "operation_direction"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    code = Column(String(40), nullable=False)
    normalized_code = Column(String(40), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(40), nullable=False, default="DOCK")
    operation_direction = Column(String(20), nullable=False, default="INBOUND")
    status = Column(String(20), nullable=False, default="DRAFT")
    physical_zone = Column(String(120), nullable=True)
    warehouse_location_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=True)
    timezone = Column(String(64), nullable=False)
    maximum_vehicle_length = Column(Numeric(12, 3), nullable=True)
    maximum_vehicle_width = Column(Numeric(12, 3), nullable=True)
    maximum_vehicle_height = Column(Numeric(12, 3), nullable=True)
    maximum_vehicle_weight = Column(Numeric(18, 3), nullable=True)
    weight_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    maximum_expected_pallets = Column(Integer, nullable=True)
    simultaneous_vehicle_capacity = Column(Integer, nullable=False, default=1)
    refrigeration_capable = Column(Boolean, nullable=False, default=False)
    temperature_control_capable = Column(Boolean, nullable=False, default=False)
    hazardous_declared_capable = Column(Boolean, nullable=False, default=False)
    oversized_capable = Column(Boolean, nullable=False, default=False)
    high_value_capable = Column(Boolean, nullable=False, default=False)
    dock_leveler_available = Column(Boolean, nullable=False, default=False)
    shelter_available = Column(Boolean, nullable=False, default=False)
    inspection_space_available = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class WarehouseDockCapabilityModel(Base):
    __tablename__ = "warehouse_dock_capabilities"
    __table_args__ = (
        UniqueConstraint("dock_id", "capability_code", "effective_from", name="uq_dock_capability_version"),
        Index("ix_dock_capabilities_dock", "dock_id"),
        Index("ix_dock_capabilities_code", "capability_code"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    capability_code = Column(String(60), nullable=False)
    value_type = Column(String(20), nullable=False)
    value_data = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WarehouseDockOperatingWindowModel(Base):
    __tablename__ = "warehouse_dock_operating_windows"
    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_dock_window_day"),
        CheckConstraint("start_local_time < end_local_time", name="ck_dock_window_time_order"),
        Index("ix_dock_windows_dock_day", "dock_id", "day_of_week"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_local_time = Column(Time, nullable=False)
    end_local_time = Column(Time, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WarehouseDockBlackoutModel(Base):
    __tablename__ = "warehouse_dock_blackouts"
    __table_args__ = (
        CheckConstraint("starts_at < ends_at", name="ck_dock_blackout_time_order"),
        Index("ix_dock_blackouts_dock_time", "dock_id", "starts_at", "ends_at"),
        Index("ix_dock_blackouts_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    reason_code = Column(String(40), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cancelled_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)


class InboundDockQueueEntryModel(Base):
    __tablename__ = "inbound_dock_queue_entries"
    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_dock_queue_row_version"),
        Index("ix_dock_queue_warehouse_status", "warehouse_id", "queue_status"),
        Index("ix_dock_queue_priority_time", "priority", "queued_at"),
        Index("ix_dock_queue_gate", "gate_check_in_id"),
        Index("uq_dock_queue_active_gate", "gate_check_in_id", unique=True, postgresql_where=text(_ACTIVE_QUEUE_SQL), sqlite_where=text(_ACTIVE_QUEUE_SQL)),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    vehicle_id = Column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=True)
    observed_plate_snapshot = Column(String(40), nullable=False)
    supplier_snapshot = Column(JSONB, nullable=True)
    carrier_snapshot = Column(JSONB, nullable=True)
    priority = Column(String(20), nullable=False, default="NORMAL")
    priority_reason = Column(Text, nullable=True)
    queue_status = Column(String(20), nullable=False, default="WAITING")
    gate_cleared_at = Column(DateTime(timezone=True), nullable=False)
    queued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ready_for_assignment_at = Column(DateTime(timezone=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removal_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class DockAssignmentPlanModel(Base):
    __tablename__ = "dock_assignment_plans"
    __table_args__ = (
        UniqueConstraint("organization_id", "assignment_hash", name="uq_dock_plan_hash"),
        Index("ix_dock_plans_gate", "gate_check_in_id"),
        Index("ix_dock_plans_expires", "expires_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    queue_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_queue_entries.id", ondelete="RESTRICT"), nullable=False)
    proposed_dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=True)
    requested_interval = Column(JSONB, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    required_capabilities = Column(JSONB, nullable=False, default=list)
    priority = Column(String(20), nullable=False)
    assignment_mode = Column(String(30), nullable=False)
    eligible_docks = Column(JSONB, nullable=False, default=list)
    recommendation = Column(JSONB, nullable=True)
    conflicts = Column(JSONB, nullable=False, default=list)
    warnings = Column(JSONB, nullable=False, default=list)
    assignment_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)


class InboundDockAssignmentModel(Base):
    __tablename__ = "inbound_dock_assignments"
    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_dock_assignment_row_version"),
        CheckConstraint("planned_end IS NULL OR planned_start IS NULL OR planned_start < planned_end", name="ck_dock_assignment_plan_order"),
        CheckConstraint("capacity_slot >= 1", name="ck_dock_assignment_slot"),
        Index("ix_dock_assignments_warehouse", "warehouse_id"),
        Index("ix_dock_assignments_dock_status", "dock_id", "status"),
        Index("ix_dock_assignments_gate", "gate_check_in_id"),
        Index("ix_dock_assignments_vehicle", "vehicle_id"),
        Index("ix_dock_assignments_assigned_at", "assigned_at"),
        Index("ix_dock_assignments_arrived_at", "dock_arrived_at"),
        Index("uq_dock_assignment_active_gate", "gate_check_in_id", unique=True, postgresql_where=text(_ACTIVE_ASSIGNMENT_SQL), sqlite_where=text(_ACTIVE_ASSIGNMENT_SQL)),
        Index("uq_dock_assignment_active_vehicle", "vehicle_id", unique=True, postgresql_where=text(f"vehicle_id IS NOT NULL AND {_ACTIVE_ASSIGNMENT_SQL}"), sqlite_where=text(f"vehicle_id IS NOT NULL AND {_ACTIVE_ASSIGNMENT_SQL}")),
        Index("uq_dock_assignment_active_slot", "dock_id", "capacity_slot", unique=True, postgresql_where=text(_ACTIVE_ASSIGNMENT_SQL), sqlite_where=text(_ACTIVE_ASSIGNMENT_SQL)),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    queue_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_queue_entries.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    vehicle_id = Column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=True)
    observed_plate_snapshot = Column(String(40), nullable=False)
    status = Column(String(40), nullable=False, default="ASSIGNED")
    assignment_mode = Column(String(30), nullable=False)
    assignment_reason = Column(Text, nullable=False)
    compatibility_snapshot = Column(JSONB, nullable=False)
    assignment_hash = Column(String(64), nullable=False)
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    capacity_slot = Column(Integer, nullable=False, default=1)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_by_snapshot = Column(JSONB, nullable=False)
    movement_started_at = Column(DateTime(timezone=True), nullable=True)
    dock_arrived_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    reassigned_from_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=True)
    superseded_by_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class DockOccupancyIntervalModel(Base):
    __tablename__ = "dock_occupancy_intervals"
    __table_args__ = (
        CheckConstraint("occupied_until IS NULL OR occupied_from <= occupied_until", name="ck_dock_occupancy_order"),
        Index("ix_dock_occupancy_dock_status", "dock_id", "status"),
        Index("uq_dock_occupancy_active_assignment", "dock_assignment_id", unique=True, postgresql_where=text("status = 'ACTIVE'"), sqlite_where=text("status = 'ACTIVE'")),
        Index("uq_dock_occupancy_active_slot", "dock_id", "capacity_slot", unique=True, postgresql_where=text("status = 'ACTIVE'"), sqlite_where=text("status = 'ACTIVE'")),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    dock_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=False)
    vehicle_id = Column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=True)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    capacity_slot = Column(Integer, nullable=False)
    occupied_from = Column(DateTime(timezone=True), nullable=False)
    occupied_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    source = Column(String(40), nullable=False, default="DOCK_ARRIVAL")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingOperationModel(Base):
    __tablename__ = "unloading_operations"
    __table_args__ = (
        UniqueConstraint("organization_id", "operation_code", name="uq_unloading_operation_code"),
        CheckConstraint("total_pause_seconds >= 0", name="ck_unloading_pause_seconds"),
        CheckConstraint("gross_duration_seconds IS NULL OR gross_duration_seconds >= 0", name="ck_unloading_gross_seconds"),
        CheckConstraint("net_duration_seconds IS NULL OR net_duration_seconds >= 0", name="ck_unloading_net_seconds"),
        CheckConstraint("row_version >= 1", name="ck_unloading_row_version"),
        Index("ix_unloading_warehouse_status", "warehouse_id", "status"),
        Index("ix_unloading_dock", "dock_id"),
        Index("ix_unloading_started", "started_at"),
        Index("ix_unloading_completed", "completed_at"),
        Index("uq_unloading_active_assignment", "dock_assignment_id", unique=True, postgresql_where=text(_ACTIVE_OPERATION_SQL), sqlite_where=text(_ACTIVE_OPERATION_SQL)),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    dock_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    operation_code = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="CREATED")
    readiness_status = Column(String(30), nullable=False, default="PENDING")
    unloading_method = Column(String(30), nullable=False)
    expected_load_summary = Column(JSONB, nullable=True)
    special_requirements_snapshot = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    started_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    started_by_snapshot = Column(JSONB, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    completed_by_snapshot = Column(JSONB, nullable=True)
    aborted_at = Column(DateTime(timezone=True), nullable=True)
    aborted_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    abort_reason = Column(Text, nullable=True)
    total_pause_seconds = Column(Integer, nullable=False, default=0)
    gross_duration_seconds = Column(Integer, nullable=True)
    net_duration_seconds = Column(Integer, nullable=True)
    release_required = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class UnloadingReadinessCheckDefinitionModel(Base):
    __tablename__ = "unloading_readiness_check_definitions"
    __table_args__ = (
        UniqueConstraint("organization_id", "warehouse_id", "dock_id", "check_code", name="uq_unloading_readiness_definition"),
        Index("ix_readiness_def_scope", "organization_id", "warehouse_id", "dock_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=True)
    check_code = Column(String(80), nullable=False)
    name = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    blocking_on_fail = Column(Boolean, nullable=False, default=True)
    requires_evidence = Column(Boolean, nullable=False, default=False)
    allow_override = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingReadinessCheckResultModel(Base):
    __tablename__ = "unloading_readiness_check_results"
    __table_args__ = (
        UniqueConstraint("unloading_operation_id", "check_code", name="uq_unloading_readiness_result"),
        Index("ix_readiness_result_operation", "unloading_operation_id"),
        Index("ix_readiness_result_blocking", "blocking", "result"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    check_definition_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_readiness_check_definitions.id", ondelete="RESTRICT"), nullable=False)
    check_code = Column(String(80), nullable=False)
    result = Column(String(30), nullable=False)
    observation = Column(Text, nullable=True)
    evidence_file_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="RESTRICT"), nullable=True)
    blocking = Column(Boolean, nullable=False, default=False)
    override_status = Column(String(20), nullable=False, default="NOT_REQUESTED")
    override_reason = Column(Text, nullable=True)
    override_requested_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    override_reviewed_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    checked_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingCompletionCheckDefinitionModel(Base):
    __tablename__ = "unloading_completion_check_definitions"
    __table_args__ = (UniqueConstraint("organization_id", "check_code", name="uq_unloading_completion_definition"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    check_code = Column(String(80), nullable=False)
    name = Column(String(180), nullable=False)
    order_index = Column(Integer, nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    blocking_on_fail = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingCompletionCheckResultModel(Base):
    __tablename__ = "unloading_completion_check_results"
    __table_args__ = (UniqueConstraint("unloading_operation_id", "check_code", name="uq_unloading_completion_result"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    check_definition_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_completion_check_definitions.id", ondelete="RESTRICT"), nullable=False)
    check_code = Column(String(80), nullable=False)
    result = Column(String(30), nullable=False)
    observation = Column(Text, nullable=True)
    checked_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingResponsibleAssignmentModel(Base):
    __tablename__ = "unloading_responsible_assignments"
    __table_args__ = (
        Index("ix_unloading_responsible_operation", "unloading_operation_id", "status"),
        Index("ix_unloading_responsible_user", "user_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    responsibility_type = Column(String(50), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="RESTRICT"), nullable=True)
    team_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    responsible_snapshot = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="ASSIGNED")
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingEquipmentAssignmentModel(Base):
    __tablename__ = "unloading_equipment_assignments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False, index=True)
    equipment_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    equipment_type = Column(String(40), nullable=False)
    source_type = Column(String(30), nullable=False)
    identifier_snapshot = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="ASSIGNED")
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingSealOpeningEventModel(Base):
    __tablename__ = "unloading_seal_opening_events"
    __table_args__ = (UniqueConstraint("unloading_operation_id", name="uq_unloading_seal_opening"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    gate_seal_inspection_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_seal_inspections.id", ondelete="RESTRICT"), nullable=True)
    expected_seal_number_redacted = Column(String(80), nullable=True)
    observed_seal_number_redacted = Column(String(80), nullable=True)
    prior_physical_status = Column(String(40), nullable=True)
    opening_status = Column(String(40), nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    opened_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    opened_by_snapshot = Column(JSONB, nullable=False)
    witnessed_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    photo_file_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="RESTRICT"), nullable=True)
    observation = Column(Text, nullable=True)
    anomaly_detected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UnloadingPauseModel(Base):
    __tablename__ = "unloading_pauses"
    __table_args__ = (
        UniqueConstraint("unloading_operation_id", "pause_number", name="uq_unloading_pause_number"),
        CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0", name="ck_unloading_pause_duration"),
        Index("ix_unloading_pauses_operation", "unloading_operation_id"),
        Index("ix_unloading_pauses_status_started", "status", "started_at"),
        Index("uq_unloading_pause_active", "unloading_operation_id", unique=True, postgresql_where=text("status = 'ACTIVE'"), sqlite_where=text("status = 'ACTIVE'")),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    pause_number = Column(Integer, nullable=False)
    reason_code = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    started_by_snapshot = Column(JSONB, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    ended_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    ended_by_snapshot = Column(JSONB, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    evidence_file_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DockOperationalEventModel(Base):
    __tablename__ = "dock_operational_events"
    __table_args__ = (
        Index("ix_dock_events_dock_time", "dock_id", "event_at"),
        Index("ix_dock_events_operation", "unloading_operation_id"),
        Index("ix_dock_events_type", "event_type"),
        Index("uq_dock_events_gate_sequence", "gate_check_in_id", "sequence_number", unique=True),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=True)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    dock_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=True)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=True)
    sequence_number = Column(Integer, nullable=False)
    event_type = Column(String(60), nullable=False)
    event_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    actor_snapshot = Column(JSONB, nullable=False)
    source = Column(String(40), nullable=False, default="BACKEND_COMMAND")
    payload_summary = Column(JSONB, nullable=False, default=dict)
    previous_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    correlation_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DockOperationalTimeCorrectionModel(Base):
    __tablename__ = "dock_operational_time_corrections"
    __table_args__ = (Index("ix_dock_time_corrections_resource", "resource_type", "resource_id"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(PG_UUID(as_uuid=True), nullable=False)
    field_code = Column(String(60), nullable=False)
    original_timestamp = Column(DateTime(timezone=True), nullable=False)
    proposed_timestamp = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(20), nullable=False, default="REQUESTED")
    requested_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewed_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DockOperationMetricsProjectionModel(Base):
    __tablename__ = "dock_operation_metrics_projection"
    __table_args__ = (
        UniqueConstraint("unloading_operation_id", name="uq_dock_metrics_operation"),
        Index("ix_dock_metrics_warehouse_date", "warehouse_id", "arrival_date"),
        Index("ix_dock_metrics_dock", "dock_id"),
        Index("ix_dock_metrics_quality", "data_quality_status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    dock_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouse_docks.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=False)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(PG_UUID(as_uuid=True), nullable=True)
    carrier_id = Column(PG_UUID(as_uuid=True), nullable=True)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_date = Column(Date, nullable=True)
    arrival_hour_local = Column(Integer, nullable=True)
    planned_slot_start = Column(DateTime(timezone=True), nullable=True)
    planned_slot_end = Column(DateTime(timezone=True), nullable=True)
    gate_processing_seconds = Column(Integer, nullable=True)
    dock_assignment_wait_seconds = Column(Integer, nullable=True)
    gate_to_dock_seconds = Column(Integer, nullable=True)
    dock_wait_before_unloading_seconds = Column(Integer, nullable=True)
    unloading_gross_seconds = Column(Integer, nullable=True)
    unloading_pause_seconds = Column(Integer, nullable=True)
    unloading_net_seconds = Column(Integer, nullable=True)
    dock_release_delay_seconds = Column(Integer, nullable=True)
    dock_occupancy_seconds = Column(Integer, nullable=True)
    pause_count = Column(Integer, nullable=False, default=0)
    reassignment_count = Column(Integer, nullable=False, default=0)
    data_quality_status = Column(String(30), nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    released = Column(Boolean, nullable=False, default=False)
    projection_version = Column(String(20), nullable=False, default="1.0.0")
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DockOperationExportJobModel(Base):
    __tablename__ = "dock_operation_export_jobs"
    __table_args__ = (Index("ix_dock_export_jobs_status", "status", "created_at"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True)
    export_format = Column(String(10), nullable=False)
    filters = Column(JSONB, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="PENDING")
    requested_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="RESTRICT"), nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


__all__ = [name for name in tuple(globals()) if name.endswith("Model")]
