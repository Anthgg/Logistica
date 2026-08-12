from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint("package_count > 0", name="ck_shipments_package_count_positive"),
        CheckConstraint("total_weight > 0", name="ck_shipments_weight_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tracking_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    client_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )
    origin_address: Mapped[str] = mapped_column(String(255))
    destination_address: Mapped[str] = mapped_column(String(255))
    origin_district: Mapped[str] = mapped_column(String(100))
    destination_district: Mapped[str] = mapped_column(String(100))
    package_description: Mapped[str] = mapped_column(Text)
    package_count: Mapped[int] = mapped_column(Integer)
    total_weight: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    declared_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    priority: Mapped[str] = mapped_column(
        String(20), default="normal", server_default=text("'normal'"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="registered", server_default=text("'registered'"), index=True
    )
    assigned_route_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_routes.id", ondelete="SET NULL"),
        index=True,
    )
    expected_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
