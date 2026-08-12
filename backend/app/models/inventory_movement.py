from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class InventoryMovement(Base):
    # NOTE (Phase 044): The legacy ``inventory_movements`` table is renamed to
    # ``inventory_movements_legacy`` to free the canonical name for the
    # append-only ``InventoryMovementModel``. The original columns are kept so
    # that any pre-Phase-044 data is still readable through a separate read-only
    # query path. New writes MUST go through the Phase 044 ledger.
    __tablename__ = "inventory_movements_legacy"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
        CheckConstraint(
            "resulting_stock >= 0", name="ck_inventory_movement_stock_nonnegative"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    inventory_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="RESTRICT"),
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(String(20), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    previous_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    resulting_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    reason: Mapped[str] = mapped_column(Text)
    shipment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shipments.id", ondelete="SET NULL"), index=True
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
