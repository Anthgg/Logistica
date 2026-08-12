"""SQLAlchemy ORM models for Phase 022 — Warehouses & Locations Hierarchy."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class WarehouseLocationModel(Base):
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("organization_id", "full_code", name="uq_locations_org_full_code"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    location_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_code: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    hierarchy_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    depth: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False, index=True
    )
    usage_type: Mapped[str] = mapped_column(
        String(30), default="GENERAL_STORAGE", server_default=text("'GENERAL_STORAGE'"), nullable=False
    )

    picking_priority: Mapped[int | None] = mapped_column(Integer)
    putaway_priority: Mapped[int | None] = mapped_column(Integer)

    is_pickable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_receivable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_dispatchable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_countable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    lock_reason: Mapped[str | None] = mapped_column(String(255))

    layout_x: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    layout_y: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    layout_width: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    layout_height: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    layout_rotation: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    floor_index: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    parent: Mapped["WarehouseLocationModel | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["WarehouseLocationModel"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )

    capacities: Mapped[list["WarehouseLocationCapacityModel"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    restrictions: Mapped[list["WarehouseLocationRestrictionModel"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class WarehouseLocationCapacityModel(Base):
    __tablename__ = "warehouse_location_capacities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capacity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    maximum_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False)

    warning_threshold: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    critical_threshold: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    location: Mapped["WarehouseLocationModel"] = relationship(back_populates="capacities")


class WarehouseLocationRestrictionModel(Base):
    __tablename__ = "warehouse_location_restrictions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    restriction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), default="EQUALS", server_default=text("'EQUALS'"), nullable=False)
    value_payload: Mapped[dict | None] = mapped_column(postgresql.JSONB(astext_type=text("text")))
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", server_default=text("'MEDIUM'"), nullable=False)
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False
    )

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    location: Mapped["WarehouseLocationModel"] = relationship(back_populates="restrictions")


class WarehouseLocationCodeAliasModel(Base):
    __tablename__ = "warehouse_location_code_aliases"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_full_code: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    new_full_code: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class WarehouseLayoutVersionModel(Base):
    __tablename__ = "warehouse_layout_versions"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "version", name="uq_warehouse_layout_version"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="DRAFT", server_default=text("'DRAFT'"), nullable=False
    )
    canvas_width: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1000.00"), nullable=False)
    canvas_height: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1000.00"), nullable=False)
    floor_count: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    approved_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    nodes: Mapped[list["WarehouseLayoutNodeModel"]] = relationship(
        back_populates="layout_version", cascade="all, delete-orphan"
    )


class WarehouseLayoutNodeModel(Base):
    __tablename__ = "warehouse_layout_nodes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    layout_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_layout_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    floor_index: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    x: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    y: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    width: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("100.00"), nullable=False)
    height: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("100.00"), nullable=False)
    rotation_degrees: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)

    shape_type: Mapped[str] = mapped_column(String(30), default="RECTANGLE", server_default=text("'RECTANGLE'"), nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    label_position: Mapped[str] = mapped_column(String(20), default="CENTER", server_default=text("'CENTER'"), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False
    )

    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    layout_version: Mapped["WarehouseLayoutVersionModel"] = relationship(back_populates="nodes")


class WarehouseLocationQRVersionModel(Base):
    __tablename__ = "warehouse_location_qr_versions"
    __table_args__ = (
        UniqueConstraint("public_reference", name="uq_location_qr_public_ref"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    qr_version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    public_reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False
    )

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    generated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
