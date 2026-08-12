"""SQLAlchemy 2.0 ORM Models for Phase 037 (Gate Control Core Domain)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.modules.logistics.gate_control.domain.enums import (
    AccessDecision,
    GateEventType,
    GateRecordStatus,
    GateStatus,
    GateType,
    SealStatus,
)


def compute_gate_content_hash(payload: dict[str, Any]) -> str:
    """Compute SHA256 content hash for deterministic audit and tamper protection."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class WarehouseGateModel(Base):
    """Represents a physical or logical gate at a warehouse facility."""

    __tablename__ = "warehouse_gates"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouse_gates_org_code"),
        CheckConstraint("row_version >= 1", name="ck_warehouse_gates_row_version_positive"),
        Index("ix_warehouse_gates_org", "organization_id"),
        Index("ix_warehouse_gates_warehouse", "warehouse_id"),
        Index("ix_warehouse_gates_status", "status"),
        Index("ix_warehouse_gates_type", "gate_type"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    gate_type: Mapped[str] = mapped_column(String(30), nullable=False, default=GateType.MAIN_ENTRY)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=GateStatus.ACTIVE)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    records = relationship("GateControlRecordModel", back_populates="gate")


class GateControlRecordModel(Base):
    """Represents an active or historic vehicle/driver access event at a gate."""

    __tablename__ = "gate_control_records"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("organization_id", "record_code", name="uq_gate_control_records_org_code"),
        CheckConstraint("row_version >= 1", name="ck_gate_control_records_row_version_positive"),
        CheckConstraint(
            "check_out_at IS NULL OR check_in_at IS NULL OR check_out_at >= check_in_at",
            name="ck_gate_records_checkout_after_checkin",
        ),
        Index("ix_gate_records_org", "organization_id"),
        Index("ix_gate_records_gate", "gate_id"),
        Index("ix_gate_records_appointment", "reception_appointment_id"),
        Index("ix_gate_records_vehicle", "vehicle_id"),
        Index("ix_gate_records_driver", "driver_id"),
        Index("ix_gate_records_guard", "guard_user_id"),
        Index("ix_gate_records_status", "status"),
        Index("ix_gate_records_arrival", "arrival_at"),
        Index("ix_gate_records_plate", "plate_observed"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    record_code: Mapped[str] = mapped_column(String(50), nullable=False)
    gate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_gates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reception_appointment_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reception_appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    driver_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
    )
    guard_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, default=GateEventType.CHECK_IN)
    arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_decision: Mapped[str] = mapped_column(
        String(30), nullable=False, default=AccessDecision.PENDING
    )
    plate_observed: Mapped[str] = mapped_column(String(20), nullable=False)
    seal_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SealStatus.NOT_APPLICABLE
    )
    driver_dni_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    driver_license_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=GateRecordStatus.DRAFT)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    gate = relationship("WarehouseGateModel", back_populates="records")
    history_entries = relationship(
        "GateControlHistoryModel",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="GateControlHistoryModel.created_at.asc()",
    )


class GateControlHistoryModel(Base):
    """Audit log for status transitions and decisions in gate control records."""

    __tablename__ = "gate_control_history"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_control_history_record", "record_id"),
        Index("ix_gate_control_history_changed_by", "changed_by_user_id"),
        Index("ix_gate_control_history_created", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_control_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    record = relationship("GateControlRecordModel", back_populates="history_entries")
