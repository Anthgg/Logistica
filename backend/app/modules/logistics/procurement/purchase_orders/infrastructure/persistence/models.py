"""Phase 034 - Purchase Order ORM models.

All monetary amounts and quantities use Numeric(28, 10) — never float.
Tables use the `po_` prefix to coexist with the legacy `purchase_orders` table.
Uses classical Column() style (not mapped_column / Annotated Declarative).
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MONEY = dict(precision=28, scale=10)
_QTY   = dict(precision=28, scale=10)
_RATE  = dict(precision=12, scale=8)


# ===========================================================================
# 1. PurchaseOrder — main aggregate root
# ===========================================================================
class PurchaseOrderModel(Base):
    __tablename__ = "po_purchase_orders"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "normalized_purchase_order_code",
            name="uq_po_orders_org_code",
        ),
        CheckConstraint("grand_total >= 0", name="ck_po_orders_grand_total_non_negative"),
        CheckConstraint(
            "status IN ('DRAFT','VALIDATED','PENDING_APPROVAL','RETURNED_FOR_CHANGES',"
            "'APPROVED','ISSUING','ISSUED','DISPATCHING','SENT','ACKNOWLEDGED',"
            "'REJECTED_BY_SUPPLIER','CANCELLED','CLOSED','ARCHIVED')",
            name="ck_po_orders_status",
        ),
        CheckConstraint(
            "approval_status IN ('NOT_SUBMITTED','PENDING','APPROVED','REJECTED','RETURNED','SUPERSEDED')",
            name="ck_po_orders_approval_status",
        ),
        CheckConstraint(
            "issuance_status IN ('NOT_ISSUED','ISSUING','ISSUED','FAILED','CANCELLED')",
            name="ck_po_orders_issuance_status",
        ),
        CheckConstraint(
            "dispatch_status IN ('NOT_SENT','QUEUED','SENDING','SENT','DELIVERED','FAILED','MANUALLY_DELIVERED')",
            name="ck_po_orders_dispatch_status",
        ),
        CheckConstraint(
            "acknowledgement_status IN ('NOT_REQUESTED','PENDING','ACKNOWLEDGED','REJECTED','EXPIRED')",
            name="ck_po_orders_acknowledgement_status",
        ),
        CheckConstraint(
            "fulfilment_status IN ('NOT_STARTED','PARTIAL_FUTURE','COMPLETE_FUTURE','CANCELLED','UNKNOWN')",
            name="ck_po_orders_fulfilment_status",
        ),
        Index("ix_po_orders_org_id", "organization_id"),
        Index("ix_po_orders_branch_id", "branch_id"),
        Index("ix_po_orders_supplier_id", "supplier_business_partner_id"),
        Index("ix_po_orders_source_decision_id", "source_decision_id"),
        Index("ix_po_orders_status", "status"),
        Index("ix_po_orders_approval_status", "approval_status"),
        Index("ix_po_orders_issuance_status", "issuance_status"),
        Index("ix_po_orders_dispatch_status", "dispatch_status"),
        Index("ix_po_orders_currency_code", "currency_code"),
        Index("ix_po_orders_expected_delivery_start", "expected_delivery_start"),
        Index("ix_po_orders_issued_at", "issued_at"),
        Index("ix_po_orders_updated_at", "updated_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Org scope
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    branch_id = Column(PG_UUID(as_uuid=True), nullable=False)

    # Document code (assigned at issuance)
    purchase_order_code = Column(String(60), nullable=True)
    normalized_purchase_order_code = Column(String(60), nullable=True)
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)
    document_series_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Supplier
    supplier_business_partner_id = Column(PG_UUID(as_uuid=True), nullable=False)
    supplier_role_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_snapshot = Column(JSONB, nullable=True)
    supplier_address_snapshot = Column(JSONB, nullable=True)
    supplier_contact_snapshot = Column(JSONB, nullable=True)

    # Source traceability
    source_decision_id = Column(PG_UUID(as_uuid=True), nullable=False)
    source_evaluation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_evaluation_run_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_quotation_round_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_purchase_requisition_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_purchase_requisition_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Currency
    currency_code = Column(String(3), nullable=False)

    # State machine — multiple orthogonal status fields
    status = Column(String(30), nullable=False, default="DRAFT")
    approval_status = Column(String(30), nullable=False, default="NOT_SUBMITTED")
    issuance_status = Column(String(30), nullable=False, default="NOT_ISSUED")
    dispatch_status = Column(String(30), nullable=False, default="NOT_SENT")
    acknowledgement_status = Column(String(30), nullable=False, default="NOT_REQUESTED")
    fulfilment_status = Column(String(30), nullable=False, default="NOT_STARTED")

    # Revision tracking
    current_revision_number = Column(Integer, nullable=False, default=1)
    active_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    issued_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Monetary summary (Decimal, calculated by backend)
    subtotal = Column(Numeric(**_MONEY), nullable=False, default=0)
    discount_total = Column(Numeric(**_MONEY), nullable=False, default=0)
    tax_total = Column(Numeric(**_MONEY), nullable=False, default=0)
    freight_total = Column(Numeric(**_MONEY), nullable=False, default=0)
    other_charges_total = Column(Numeric(**_MONEY), nullable=False, default=0)
    grand_total = Column(Numeric(**_MONEY), nullable=False, default=0)
    amount_scale = Column(Integer, nullable=False, default=2)
    rounding_mode = Column(String(20), nullable=False, default="HALF_UP")

    # Delivery
    expected_delivery_start = Column(DateTime(timezone=True), nullable=True)
    expected_delivery_end = Column(DateTime(timezone=True), nullable=True)
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    destination_address_snapshot = Column(JSONB, nullable=True)

    # Buyer
    buyer_user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    buyer_snapshot = Column(JSONB, nullable=True)
    cost_center_snapshot = Column(JSONB, nullable=True)

    # Commercial terms (summary — detail in child tables)
    payment_terms_summary = Column(Text, nullable=True)
    delivery_terms_summary = Column(Text, nullable=True)
    warranty_summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Lifecycle timestamps
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    issued_by = Column(PG_UUID(as_uuid=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(PG_UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Audit
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

    # Relationships (no Python type annotations — classical Column() style)
    revisions = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="purchase_order",
        order_by="PurchaseOrderRevisionModel.revision_number",
        foreign_keys="[PurchaseOrderRevisionModel.purchase_order_id]",
    )
    allocations = relationship(
        "PurchaseOrderSourceAllocationModel",
        back_populates="purchase_order",
        foreign_keys="[PurchaseOrderSourceAllocationModel.purchase_order_id]",
    )
    variances = relationship(
        "PurchaseOrderSourceVarianceModel",
        back_populates="purchase_order",
        foreign_keys="[PurchaseOrderSourceVarianceModel.purchase_order_id]",
    )
    approval_decisions = relationship(
        "PurchaseOrderApprovalDecisionModel",
        back_populates="purchase_order",
        order_by="PurchaseOrderApprovalDecisionModel.created_at",
        foreign_keys="[PurchaseOrderApprovalDecisionModel.purchase_order_id]",
    )
    dispatches = relationship(
        "PurchaseOrderDispatchModel",
        back_populates="purchase_order",
        foreign_keys="[PurchaseOrderDispatchModel.purchase_order_id]",
    )
    acknowledgements = relationship(
        "PurchaseOrderAcknowledgementModel",
        back_populates="purchase_order",
        foreign_keys="[PurchaseOrderAcknowledgementModel.purchase_order_id]",
    )
    amendments = relationship(
        "PurchaseOrderAmendmentModel",
        back_populates="purchase_order",
        foreign_keys="[PurchaseOrderAmendmentModel.purchase_order_id]",
    )


# ===========================================================================
# 2. PurchaseOrderRevision — immutable snapshot of a draft/approved version
# ===========================================================================
class PurchaseOrderRevisionModel(Base):
    __tablename__ = "po_purchase_order_revisions"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_id",
            "revision_number",
            name="uq_po_revisions_order_revision",
        ),
        CheckConstraint(
            "status IN ('EDITABLE','VALIDATED','PENDING_APPROVAL','APPROVED',"
            "'FROZEN','SUPERSEDED','CANCELLED')",
            name="ck_po_revisions_status",
        ),
        Index("ix_po_revisions_purchase_order_id", "purchase_order_id"),
        Index("ix_po_revisions_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="EDITABLE")

    # Immutable snapshots (frozen at approval)
    supplier_snapshot = Column(JSONB, nullable=True)
    source_snapshot = Column(JSONB, nullable=True)
    currency_code = Column(String(3), nullable=False)
    monetary_summary = Column(JSONB, nullable=True)
    destination_snapshot = Column(JSONB, nullable=True)
    terms_snapshot = Column(JSONB, nullable=True)
    delivery_schedule_snapshot = Column(JSONB, nullable=True)
    attachment_snapshot = Column(JSONB, nullable=True)

    # Integrity
    content_hash = Column(String(64), nullable=True)  # SHA-256 of canonical payload
    change_summary = Column(Text, nullable=True)
    created_from_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    validated_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    frozen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="revisions",
        foreign_keys=[purchase_order_id],
    )
    lines = relationship(
        "PurchaseOrderLineModel",
        back_populates="revision",
        order_by="PurchaseOrderLineModel.line_number",
        foreign_keys="[PurchaseOrderLineModel.purchase_order_revision_id]",
    )
    tax_components = relationship(
        "PurchaseOrderTaxComponentModel",
        back_populates="revision",
        foreign_keys="[PurchaseOrderTaxComponentModel.revision_id]",
    )
    charges = relationship(
        "PurchaseOrderChargeModel",
        back_populates="revision",
        foreign_keys="[PurchaseOrderChargeModel.revision_id]",
    )
    payment_terms = relationship(
        "PurchaseOrderPaymentTermsModel",
        back_populates="revision",
        foreign_keys="[PurchaseOrderPaymentTermsModel.revision_id]",
    )
    delivery_terms = relationship(
        "PurchaseOrderDeliveryTermsModel",
        back_populates="revision",
        foreign_keys="[PurchaseOrderDeliveryTermsModel.revision_id]",
    )
    delivery_schedules = relationship(
        "PurchaseOrderDeliveryScheduleModel",
        back_populates="revision",
        order_by="PurchaseOrderDeliveryScheduleModel.schedule_number",
        foreign_keys="[PurchaseOrderDeliveryScheduleModel.purchase_order_revision_id]",
    )


# ===========================================================================
# 3. PurchaseOrderLine — one line per product/service in the revision
# ===========================================================================
class PurchaseOrderLineModel(Base):
    __tablename__ = "po_purchase_order_lines"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_revision_id",
            "line_number",
            name="uq_po_lines_revision_line",
        ),
        CheckConstraint("ordered_quantity > 0", name="ck_po_lines_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_po_lines_price_non_negative"),
        CheckConstraint("discount_amount >= 0", name="ck_po_lines_discount_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_po_lines_total_non_negative"),
        CheckConstraint(
            "status IN ('ACTIVE','CANCELLED','SUPERSEDED')",
            name="ck_po_lines_status",
        ),
        Index("ix_po_lines_revision_id", "purchase_order_revision_id"),
        Index("ix_po_lines_product_id", "product_id"),
        Index("ix_po_lines_decision_line_id", "evaluation_decision_line_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_number = Column(Integer, nullable=False)

    # Source traceability
    source_allocation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    evaluation_decision_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    quotation_response_line_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Product (snapshot prevents mutation)
    product_id = Column(PG_UUID(as_uuid=True), nullable=True)
    product_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    sku_snapshot = Column(String(120), nullable=True)
    product_name_snapshot = Column(String(500), nullable=False)
    product_description_snapshot = Column(Text, nullable=True)
    specifications_snapshot = Column(JSONB, nullable=True)
    supplier_product_reference = Column(String(120), nullable=True)

    # Quantities (Decimal, never float)
    ordered_quantity = Column(Numeric(**_QTY), nullable=False)
    ordered_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    ordered_unit_code = Column(String(20), nullable=False)
    base_quantity = Column(Numeric(**_QTY), nullable=True)
    base_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    base_unit_code = Column(String(20), nullable=True)

    # Pricing (Decimal, source from quotation response)
    unit_price = Column(Numeric(**_MONEY), nullable=False)
    currency_code = Column(String(3), nullable=False)

    # Discount
    discount_type = Column(String(20), nullable=True)   # PERCENTAGE / FIXED_AMOUNT / NONE
    discount_value = Column(Numeric(**_RATE), nullable=True)
    discount_amount = Column(Numeric(**_MONEY), nullable=False, default=0)

    # Tax
    tax_treatment = Column(String(40), nullable=True)
    tax_amount = Column(Numeric(**_MONEY), nullable=False, default=0)

    # Additional charges
    freight_amount = Column(Numeric(**_MONEY), nullable=False, default=0)
    other_charges_amount = Column(Numeric(**_MONEY), nullable=False, default=0)

    # Totals (calculated by backend)
    line_subtotal = Column(Numeric(**_MONEY), nullable=False, default=0)
    line_total = Column(Numeric(**_MONEY), nullable=False, default=0)

    # Delivery
    required_date = Column(DateTime(timezone=True), nullable=True)
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    destination_snapshot = Column(JSONB, nullable=True)
    delivery_terms = Column(Text, nullable=True)
    warranty_terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # State
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, default=1)

    # Relationships
    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="lines",
        foreign_keys=[purchase_order_revision_id],
    )


# ===========================================================================
# 4. PurchaseOrderSourceAllocation — links decision lines to PO lines
# ===========================================================================
class PurchaseOrderSourceAllocationModel(Base):
    __tablename__ = "po_source_allocations"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("allocated_quantity > 0", name="ck_po_alloc_qty_positive"),
        CheckConstraint(
            "status IN ('RESERVED','ACTIVE','CANCELLED','RELEASED')",
            name="ck_po_alloc_status",
        ),
        Index("ix_po_alloc_decision_line_id", "evaluation_decision_line_id"),
        Index("ix_po_alloc_po_line_id", "purchase_order_line_id"),
        Index("ix_po_alloc_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_line_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Source identifiers
    evaluation_decision_id = Column(PG_UUID(as_uuid=True), nullable=False)
    evaluation_decision_line_id = Column(PG_UUID(as_uuid=True), nullable=False)
    quotation_response_id = Column(PG_UUID(as_uuid=True), nullable=True)
    quotation_response_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    requisition_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_business_partner_id = Column(PG_UUID(as_uuid=True), nullable=False)

    # Quantities (Decimal)
    allocated_quantity = Column(Numeric(**_QTY), nullable=False)
    allocated_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    allocated_unit_code = Column(String(20), nullable=False)
    allocated_base_quantity = Column(Numeric(**_QTY), nullable=True)

    # Source pricing (immutable copy from decision line)
    source_unit_price = Column(Numeric(**_MONEY), nullable=False)
    source_currency_code = Column(String(3), nullable=False)
    source_line_total = Column(Numeric(**_MONEY), nullable=False)

    status = Column(String(20), nullable=False, default="RESERVED")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="allocations",
        foreign_keys=[purchase_order_id],
    )


# ===========================================================================
# 5. PurchaseOrderSourceVariance — deviations from the original proposal
# ===========================================================================
class PurchaseOrderSourceVarianceModel(Base):
    __tablename__ = "po_source_variances"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "variance_type IN ('QUANTITY_REDUCTION','DELIVERY_DATE_ADJUSTMENT',"
            "'DESTINATION_ADJUSTMENT','TAX_CLARIFICATION','FREIGHT_CLARIFICATION',"
            "'ROUNDING_ADJUSTMENT','COMMERCIAL_TERM_CLARIFICATION','PRICE_EXCEPTION','OTHER')",
            name="ck_po_variance_type",
        ),
        CheckConstraint(
            "status IN ('DETECTED','JUSTIFIED','APPROVED','REJECTED','SUPERSEDED')",
            name="ck_po_variance_status",
        ),
        Index("ix_po_variance_purchase_order_id", "purchase_order_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    line_id = Column(PG_UUID(as_uuid=True), nullable=True)

    variance_type = Column(String(40), nullable=False)
    source_value = Column(JSONB, nullable=True)
    proposed_value = Column(JSONB, nullable=True)
    monetary_impact = Column(Numeric(**_MONEY), nullable=True)
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="DETECTED")

    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="variances",
        foreign_keys=[purchase_order_id],
    )


# ===========================================================================
# 6. PurchaseOrderTaxComponent — per-line or header tax detail
# ===========================================================================
class PurchaseOrderTaxComponentModel(Base):
    __tablename__ = "po_tax_components"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("tax_rate >= 0", name="ck_po_tax_rate_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_po_tax_amount_non_negative"),
        CheckConstraint(
            "tax_category IN ('GENERAL_SALES_TAX','WITHHOLDING_REFERENCE',"
            "'PERCEPTION_REFERENCE','EXEMPT','UNAFFECTED','OTHER')",
            name="ck_po_tax_category",
        ),
        Index("ix_po_tax_revision_id", "revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_id = Column(PG_UUID(as_uuid=True), nullable=True)

    tax_code = Column(String(20), nullable=False)
    tax_name = Column(String(100), nullable=False)
    tax_category = Column(String(40), nullable=False)
    tax_rate = Column(Numeric(**_RATE), nullable=False)
    taxable_base = Column(Numeric(**_MONEY), nullable=False)
    tax_amount = Column(Numeric(**_MONEY), nullable=False)
    included_in_price = Column(Boolean, nullable=False, default=False)
    source_type = Column(String(40), nullable=True)
    source_reference = Column(String(120), nullable=True)
    calculation_method = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="tax_components",
        foreign_keys=[revision_id],
    )


# ===========================================================================
# 7. PurchaseOrderCharge — freight, insurance, handling, etc.
# ===========================================================================
class PurchaseOrderChargeModel(Base):
    __tablename__ = "po_charges"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_po_charge_amount_non_negative"),
        CheckConstraint(
            "charge_type IN ('FREIGHT','INSURANCE','PACKAGING','HANDLING',"
            "'INSTALLATION','SERVICE','OTHER')",
            name="ck_po_charge_type",
        ),
        Index("ix_po_charge_revision_id", "revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_id = Column(PG_UUID(as_uuid=True), nullable=True)

    charge_type = Column(String(30), nullable=False)
    description = Column(String(300), nullable=False)
    amount = Column(Numeric(**_MONEY), nullable=False)
    currency_code = Column(String(3), nullable=False)
    taxable = Column(Boolean, nullable=False, default=False)
    tax_code = Column(String(20), nullable=True)
    source_type = Column(String(40), nullable=True)
    source_reference = Column(String(120), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="charges",
        foreign_keys=[revision_id],
    )


# ===========================================================================
# 8. PurchaseOrderPaymentTerms
# ===========================================================================
class PurchaseOrderPaymentTermsModel(Base):
    __tablename__ = "po_payment_terms"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "term_type IN ('CASH','CREDIT','ADVANCE_AND_BALANCE','MILESTONES',"
            "'AGAINST_DELIVERY','AGAINST_ACCEPTANCE','OTHER')",
            name="ck_po_pt_term_type",
        ),
        CheckConstraint(
            "advance_percentage IS NULL OR (advance_percentage >= 0 AND advance_percentage <= 100)",
            name="ck_po_pt_advance_pct",
        ),
        CheckConstraint(
            "retention_percentage IS NULL OR (retention_percentage >= 0 AND retention_percentage <= 100)",
            name="ck_po_pt_retention_pct",
        ),
        Index("ix_po_pt_revision_id", "revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    term_type = Column(String(30), nullable=False)
    payment_method = Column(String(60), nullable=True)
    credit_days = Column(Integer, nullable=True)
    advance_percentage = Column(Numeric(**_RATE), nullable=True)
    milestone_schedule = Column(JSONB, nullable=True)
    payment_reference = Column(String(120), nullable=True)
    bank_instruction_reference = Column(String(120), nullable=True)
    retention_percentage = Column(Numeric(**_RATE), nullable=True)
    notes = Column(Text, nullable=True)
    source_type = Column(String(40), nullable=True)
    source_reference = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="payment_terms",
        foreign_keys=[revision_id],
    )


# ===========================================================================
# 9. PurchaseOrderDeliveryTerms
# ===========================================================================
class PurchaseOrderDeliveryTermsModel(Base):
    __tablename__ = "po_delivery_terms"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_po_dt_revision_id", "revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    delivery_mode = Column(String(40), nullable=True)
    freight_responsibility = Column(String(40), nullable=True)
    delivery_location_type = Column(String(40), nullable=True)
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    destination_address_snapshot = Column(JSONB, nullable=True)
    partial_delivery_allowed = Column(Boolean, nullable=False, default=True)
    early_delivery_allowed = Column(Boolean, nullable=False, default=True)
    late_delivery_tolerance_days = Column(Integer, nullable=True)
    receiving_hours = Column(String(100), nullable=True)
    appointment_required = Column(Boolean, nullable=False, default=False)
    packaging_requirements = Column(Text, nullable=True)
    labeling_requirements = Column(Text, nullable=True)
    documentation_requirements = Column(Text, nullable=True)
    incoterm_code = Column(String(10), nullable=True)
    transfer_of_risk_reference = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="delivery_terms",
        foreign_keys=[revision_id],
    )


# ===========================================================================
# 10. PurchaseOrderDeliverySchedule — partial delivery planning
# ===========================================================================
class PurchaseOrderDeliveryScheduleModel(Base):
    __tablename__ = "po_delivery_schedules"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_revision_id",
            "schedule_number",
            name="uq_po_schedules_revision_number",
        ),
        CheckConstraint(
            "status IN ('PLANNED','CONFIRMED','RESCHEDULED','CANCELLED','COMPLETED_FUTURE')",
            name="ck_po_schedule_status",
        ),
        Index("ix_po_sched_revision_id", "purchase_order_revision_id"),
        Index("ix_po_sched_planned_date", "planned_delivery_date"),
        Index("ix_po_sched_dest_warehouse_id", "destination_warehouse_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    schedule_number = Column(Integer, nullable=False)

    planned_delivery_date = Column(DateTime(timezone=True), nullable=False)
    planned_delivery_start_time = Column(DateTime(timezone=True), nullable=True)
    planned_delivery_end_time = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(60), nullable=False, default="UTC")
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    destination_address_snapshot = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="PLANNED")
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    revision = relationship(
        "PurchaseOrderRevisionModel",
        back_populates="delivery_schedules",
        foreign_keys=[purchase_order_revision_id],
    )
    schedule_lines = relationship(
        "PurchaseOrderDeliveryScheduleLineModel",
        back_populates="delivery_schedule",
        foreign_keys="[PurchaseOrderDeliveryScheduleLineModel.delivery_schedule_id]",
    )


# ===========================================================================
# 11. PurchaseOrderDeliveryScheduleLine
# ===========================================================================
class PurchaseOrderDeliveryScheduleLineModel(Base):
    __tablename__ = "po_delivery_schedule_lines"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "scheduled_quantity > 0",
            name="ck_po_sched_line_qty_positive",
        ),
        Index("ix_po_sched_line_schedule_id", "delivery_schedule_id"),
        Index("ix_po_sched_line_po_line_id", "purchase_order_line_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    delivery_schedule_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_delivery_schedules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_line_id = Column(PG_UUID(as_uuid=True), nullable=False)

    scheduled_quantity = Column(Numeric(**_QTY), nullable=False)
    scheduled_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    scheduled_unit_code = Column(String(20), nullable=False)
    scheduled_base_quantity = Column(Numeric(**_QTY), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    delivery_schedule = relationship(
        "PurchaseOrderDeliveryScheduleModel",
        back_populates="schedule_lines",
        foreign_keys=[delivery_schedule_id],
    )


# ===========================================================================
# 12. PurchaseOrderApprovalDecision
# ===========================================================================
class PurchaseOrderApprovalDecisionModel(Base):
    __tablename__ = "po_approval_decisions"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "decision_type IN ('APPROVE','REJECT','RETURN_FOR_CHANGES','CANCEL_APPROVAL')",
            name="ck_po_approval_decision_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE','SUPERSEDED','CANCELLED')",
            name="ck_po_approval_status_val",
        ),
        Index("ix_po_approval_purchase_order_id", "purchase_order_id"),
        Index("ix_po_approval_revision_id", "revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_id = Column(PG_UUID(as_uuid=True), nullable=False)

    policy_code = Column(String(80), nullable=False)
    policy_version = Column(String(20), nullable=False)
    decision_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    decided_by = Column(PG_UUID(as_uuid=True), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason = Column(Text, nullable=True)
    conditions = Column(JSONB, nullable=True)
    step_number = Column(Integer, nullable=False, default=1)
    is_final = Column(Boolean, nullable=False, default=True)
    supersedes_decision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="approval_decisions",
        foreign_keys=[purchase_order_id],
    )


# ===========================================================================
# 13. PurchaseOrderDispatch — dispatch record per send attempt batch
# ===========================================================================
class PurchaseOrderDispatchModel(Base):
    __tablename__ = "po_dispatches"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "channel IN ('EMAIL','SECURE_PORTAL','EMAIL_AND_PORTAL','MANUAL','API_AUTHORIZED')",
            name="ck_po_dispatch_channel",
        ),
        CheckConstraint(
            "status IN ('QUEUED','SENDING','SENT','DELIVERED','FAILED','MANUALLY_DELIVERED','CANCELLED')",
            name="ck_po_dispatch_status",
        ),
        Index("ix_po_dispatch_purchase_order_id", "purchase_order_id"),
        Index("ix_po_dispatch_status", "status"),
        Index("ix_po_dispatch_provider_message_id", "provider_message_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_id = Column(PG_UUID(as_uuid=True), nullable=False)
    contact_snapshot = Column(JSONB, nullable=True)

    channel = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="QUEUED")
    provider_message_id = Column(String(200), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(60), nullable=True)
    failure_summary = Column(Text, nullable=True)

    manually_delivered_at = Column(DateTime(timezone=True), nullable=True)
    manually_delivered_by = Column(PG_UUID(as_uuid=True), nullable=True)
    manual_delivery_reference = Column(String(200), nullable=True)

    acknowledgement_requested = Column(Boolean, nullable=False, default=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="dispatches",
        foreign_keys=[purchase_order_id],
    )
    delivery_attempts = relationship(
        "PurchaseOrderDeliveryAttemptModel",
        back_populates="dispatch",
        order_by="PurchaseOrderDeliveryAttemptModel.attempt_number",
        foreign_keys="[PurchaseOrderDeliveryAttemptModel.dispatch_id]",
    )


# ===========================================================================
# 14. PurchaseOrderDeliveryAttempt — individual send attempt log
# ===========================================================================
class PurchaseOrderDeliveryAttemptModel(Base):
    __tablename__ = "po_delivery_attempts"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED','SENDING','ACCEPTED_BY_PROVIDER','DELIVERED',"
            "'BOUNCED','REJECTED','FAILED','CANCELLED','UNKNOWN')",
            name="ck_po_attempt_status",
        ),
        Index("ix_po_attempt_dispatch_id", "dispatch_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dispatch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_dispatches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number = Column(Integer, nullable=False)
    channel = Column(String(30), nullable=False)
    provider = Column(String(60), nullable=True)
    provider_message_id = Column(String(200), nullable=True)
    status = Column(String(30), nullable=False, default="QUEUED")

    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(60), nullable=True)
    failure_summary = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    dispatch = relationship(
        "PurchaseOrderDispatchModel",
        back_populates="delivery_attempts",
        foreign_keys=[dispatch_id],
    )


# ===========================================================================
# 15. PurchaseOrderAcknowledgement — supplier acknowledgement record
# ===========================================================================
class PurchaseOrderAcknowledgementModel(Base):
    __tablename__ = "po_acknowledgements"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint(
            "acknowledgement_type IN ('RECEIPT_CONFIRMATION','FULL_ACCEPTANCE',"
            "'ACCEPTANCE_WITH_OBSERVATIONS','REJECTION','REQUEST_FOR_CLARIFICATION')",
            name="ck_po_ack_type",
        ),
        CheckConstraint(
            "status IN ('RECEIVED','VALIDATED','REJECTED','SUPERSEDED')",
            name="ck_po_ack_status",
        ),
        Index("ix_po_ack_purchase_order_id", "purchase_order_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dispatch_id = Column(PG_UUID(as_uuid=True), nullable=True)

    acknowledgement_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="RECEIVED")
    supplier_reference = Column(String(200), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=False)
    acknowledgement_channel = Column(String(30), nullable=False)
    acknowledged_by_name = Column(String(200), nullable=True)
    comments = Column(Text, nullable=True)
    file_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    received_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="acknowledgements",
        foreign_keys=[purchase_order_id],
    )


# ===========================================================================
# 16. PurchaseOrderAmendment — post-issuance modifications
# ===========================================================================
class PurchaseOrderAmendmentModel(Base):
    __tablename__ = "po_amendments"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_id",
            "amendment_number",
            name="uq_po_amendments_order_number",
        ),
        CheckConstraint(
            "amendment_type IN ('QUANTITY_REDUCTION','DELIVERY_RESCHEDULE',"
            "'DESTINATION_CHANGE','TERM_CHANGE','PRICE_CHANGE_WITH_NEW_DECISION',"
            "'CANCELLATION','OTHER')",
            name="ck_po_amendment_type",
        ),
        CheckConstraint(
            "status IN ('DRAFT','PENDING_APPROVAL','APPROVED','ISSUED','CANCELLED','REJECTED')",
            name="ck_po_amendment_status",
        ),
        Index("ix_po_amendment_purchase_order_id", "purchase_order_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amendment_number = Column(Integer, nullable=False)
    amendment_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    reason = Column(Text, nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    previous_snapshot_hash = Column(String(64), nullable=True)
    proposed_changes = Column(JSONB, nullable=True)
    monetary_impact = Column(Numeric(**_MONEY), nullable=True)
    schedule_impact = Column(JSONB, nullable=True)
    requires_supplier_acceptance = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(30), nullable=True)
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    issued_at = Column(DateTime(timezone=True), nullable=True)

    purchase_order = relationship(
        "PurchaseOrderModel",
        back_populates="amendments",
        foreign_keys=[purchase_order_id],
    )
