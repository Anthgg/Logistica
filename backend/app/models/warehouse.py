from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.branch import Branch


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("branch_id", "code", name="uq_warehouses_branch_code"),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
            name="chk_warehouses_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
            name="chk_warehouses_longitude",
        ),
        CheckConstraint(
            "(uses_branch_location AND latitude IS NULL AND longitude IS NULL) "
            "OR (NOT uses_branch_location AND latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="chk_warehouses_location_mode",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(String)
    warehouse_type: Mapped[str] = mapped_column(
        String(30), default="general", server_default=text("'general'"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(String(255))
    uses_branch_location: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    address_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organization_addresses.id", ondelete="SET NULL"),
        nullable=True,
    )
    district: Mapped[str | None] = mapped_column(String(100))
    province: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    capacity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False
    )
    layout_status: Mapped[str] = mapped_column(
        String(20), default="DRAFT", server_default=text("'DRAFT'"), nullable=False
    )
    manager_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    operating_hours: Mapped[dict | None] = mapped_column(postgresql.JSONB(astext_type=text("text")))
    temperature_controlled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    hazardous_materials_allowed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    cross_dock_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    receiving_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    dispatch_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    inventory_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    branch: Mapped["Branch | None"] = relationship(back_populates="warehouses")

    @property
    def effective_latitude(self) -> Decimal | None:
        if self.uses_branch_location:
            return self.branch.latitude if self.branch is not None else None
        return self.latitude

    @property
    def effective_longitude(self) -> Decimal | None:
        if self.uses_branch_location:
            return self.branch.longitude if self.branch is not None else None
        return self.longitude

    @property
    def location_source(self) -> str:
        return "BRANCH" if self.uses_branch_location else "WAREHOUSE"
