"""Persistence models for purchase orders."""

from uuid import uuid4

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "order_number",
            name="uq_purchase_orders_org_number",
        ),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_number = Column(String(40), nullable=False)
    currency_code = Column(String(3), nullable=False, default="PEN")
    subtotal_amount = Column(Numeric(18, 4), nullable=False, default=0)
    tax_amount = Column(Numeric(18, 4), nullable=False, default=0)
    total_amount = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="DRAFT", index=True)
    expected_delivery_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    issued_by = Column(PG_UUID(as_uuid=True), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    annulled_by = Column(PG_UUID(as_uuid=True), nullable=True)
    annulled_at = Column(DateTime(timezone=True), nullable=True)
    annulment_reason = Column(Text, nullable=True)
    row_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    supplier = relationship("BusinessPartnerModel")
    lines = relationship(
        "PurchaseOrderLineModel",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLineModel.line_number",
    )

    @property
    def supplier_name(self) -> str:
        return self.supplier.legal_name


class PurchaseOrderLineModel(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_id",
            "line_number",
            name="uq_purchase_order_lines_order_number",
        ),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    product_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    description = Column(String(300), nullable=False)
    unit_code = Column(String(20), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False)
    unit_price = Column(Numeric(18, 6), nullable=False)
    tax_rate = Column(Numeric(7, 4), nullable=False, default=0)
    subtotal_amount = Column(Numeric(18, 4), nullable=False)
    tax_amount = Column(Numeric(18, 4), nullable=False)
    total_amount = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    purchase_order = relationship("PurchaseOrderModel", back_populates="lines")
    product = relationship("ProductModel")
