from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class RouteShipment(Base):
    __tablename__ = "route_shipments"
    __table_args__ = (
        UniqueConstraint("route_id", "shipment_id", name="uq_route_shipment"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_routes.id", ondelete="CASCADE"),
        index=True,
    )
    shipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    assigned_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
