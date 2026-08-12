"""Phase 034 - Purchase Orders.

Revision ID: w340110034dc
Revises: v330110033dc
Create Date: 2026-07-31 05:30:00.000000

Creates 16 new tables with the `po_` prefix for the Phase 034 purchase order
domain. The legacy `purchase_orders` and `purchase_order_lines` tables are NOT
modified to preserve production data integrity.

Monetary amounts: Numeric(28, 10) — never float.
Quantities:       Numeric(28, 10) — never float.
Tax rates:        Numeric(12, 8).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
revision: str = "w340110034dc"
down_revision: str = "v330110033dc"
branch_labels = None
depends_on = None
# ---------------------------------------------------------------------------

_PG = op.get_bind().dialect.name == "postgresql" if False else True  # evaluated at runtime


def _jsonb():
    """Return JSONB for PostgreSQL, JSON for SQLite (tests)."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB()
    return sa.JSON()


def _uuid():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # ------------------------------------------------------------------
    # 1. po_purchase_orders
    # ------------------------------------------------------------------
    op.create_table(
        "po_purchase_orders",
        sa.Column("id", _uuid(), primary_key=True),
        # Scope
        sa.Column("organization_id", _uuid(), nullable=False),
        sa.Column("branch_id", _uuid(), nullable=False),
        # Document code
        sa.Column("purchase_order_code", sa.String(60), nullable=True),
        sa.Column("normalized_purchase_order_code", sa.String(60), nullable=True),
        sa.Column("document_instance_id", _uuid(), nullable=True),
        sa.Column("document_series_id", _uuid(), nullable=True),
        # Supplier
        sa.Column("supplier_business_partner_id", _uuid(), nullable=False),
        sa.Column("supplier_role_id", _uuid(), nullable=True),
        sa.Column("supplier_snapshot", _jsonb(), nullable=True),
        sa.Column("supplier_address_snapshot", _jsonb(), nullable=True),
        sa.Column("supplier_contact_snapshot", _jsonb(), nullable=True),
        # Source traceability
        sa.Column("source_decision_id", _uuid(), nullable=False),
        sa.Column("source_evaluation_id", _uuid(), nullable=True),
        sa.Column("source_evaluation_run_id", _uuid(), nullable=True),
        sa.Column("source_quotation_round_id", _uuid(), nullable=True),
        sa.Column("source_purchase_requisition_id", _uuid(), nullable=True),
        sa.Column("source_purchase_requisition_revision_id", _uuid(), nullable=True),
        # Currency
        sa.Column("currency_code", sa.String(3), nullable=False),
        # State machine
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("approval_status", sa.String(30), nullable=False, server_default="NOT_SUBMITTED"),
        sa.Column("issuance_status", sa.String(30), nullable=False, server_default="NOT_ISSUED"),
        sa.Column("dispatch_status", sa.String(30), nullable=False, server_default="NOT_SENT"),
        sa.Column("acknowledgement_status", sa.String(30), nullable=False, server_default="NOT_REQUESTED"),
        sa.Column("fulfilment_status", sa.String(30), nullable=False, server_default="NOT_STARTED"),
        # Revision tracking
        sa.Column("current_revision_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("active_revision_id", _uuid(), nullable=True),
        sa.Column("approved_revision_id", _uuid(), nullable=True),
        sa.Column("issued_revision_id", _uuid(), nullable=True),
        # Monetary summary — Numeric(28,10) for exact Decimal
        sa.Column("subtotal", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("discount_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("freight_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("other_charges_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("amount_scale", sa.Integer, nullable=False, server_default="2"),
        sa.Column("rounding_mode", sa.String(20), nullable=False, server_default="HALF_UP"),
        # Delivery
        sa.Column("expected_delivery_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_delivery_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("destination_warehouse_id", _uuid(), nullable=True),
        sa.Column("destination_address_snapshot", _jsonb(), nullable=True),
        # Buyer
        sa.Column("buyer_user_id", _uuid(), nullable=False),
        sa.Column("buyer_snapshot", _jsonb(), nullable=True),
        sa.Column("cost_center_snapshot", _jsonb(), nullable=True),
        # Terms summary
        sa.Column("payment_terms_summary", sa.Text, nullable=True),
        sa.Column("delivery_terms_summary", sa.Text, nullable=True),
        sa.Column("warranty_summary", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        # Lifecycle
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", _uuid(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by", _uuid(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", _uuid(), nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        # Audit
        sa.Column("created_by", _uuid(), nullable=False),
        sa.Column("updated_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
    )
    # Unique + check constraints
    op.create_unique_constraint(
        "uq_po_orders_org_code",
        "po_purchase_orders",
        ["organization_id", "normalized_purchase_order_code"],
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_orders_grand_total_non_negative",
            "po_purchase_orders",
            "grand_total >= 0",
        )
        op.create_check_constraint(
            "ck_po_orders_status",
            "po_purchase_orders",
            "status IN ('DRAFT','VALIDATED','PENDING_APPROVAL','RETURNED_FOR_CHANGES',"
            "'APPROVED','ISSUING','ISSUED','DISPATCHING','SENT','ACKNOWLEDGED',"
            "'REJECTED_BY_SUPPLIER','CANCELLED','CLOSED','ARCHIVED')",
        )
        op.create_check_constraint(
            "ck_po_orders_approval_status",
            "po_purchase_orders",
            "approval_status IN ('NOT_SUBMITTED','PENDING','APPROVED','REJECTED','RETURNED','SUPERSEDED')",
        )
        op.create_check_constraint(
            "ck_po_orders_issuance_status",
            "po_purchase_orders",
            "issuance_status IN ('NOT_ISSUED','ISSUING','ISSUED','FAILED','CANCELLED')",
        )
        op.create_check_constraint(
            "ck_po_orders_dispatch_status",
            "po_purchase_orders",
            "dispatch_status IN ('NOT_SENT','QUEUED','SENDING','SENT','DELIVERED','FAILED','MANUALLY_DELIVERED')",
        )
        op.create_check_constraint(
            "ck_po_orders_acknowledgement_status",
            "po_purchase_orders",
            "acknowledgement_status IN ('NOT_REQUESTED','PENDING','ACKNOWLEDGED','REJECTED','EXPIRED')",
        )
        op.create_check_constraint(
            "ck_po_orders_fulfilment_status",
            "po_purchase_orders",
            "fulfilment_status IN ('NOT_STARTED','PARTIAL_FUTURE','COMPLETE_FUTURE','CANCELLED','UNKNOWN')",
        )
    # Indexes
    op.create_index("ix_po_orders_org_id", "po_purchase_orders", ["organization_id"])
    op.create_index("ix_po_orders_branch_id", "po_purchase_orders", ["branch_id"])
    op.create_index("ix_po_orders_supplier_id", "po_purchase_orders", ["supplier_business_partner_id"])
    op.create_index("ix_po_orders_source_decision_id", "po_purchase_orders", ["source_decision_id"])
    op.create_index("ix_po_orders_status", "po_purchase_orders", ["status"])
    op.create_index("ix_po_orders_approval_status", "po_purchase_orders", ["approval_status"])
    op.create_index("ix_po_orders_issuance_status", "po_purchase_orders", ["issuance_status"])
    op.create_index("ix_po_orders_dispatch_status", "po_purchase_orders", ["dispatch_status"])
    op.create_index("ix_po_orders_currency_code", "po_purchase_orders", ["currency_code"])
    op.create_index("ix_po_orders_expected_delivery_start", "po_purchase_orders", ["expected_delivery_start"])
    op.create_index("ix_po_orders_issued_at", "po_purchase_orders", ["issued_at"])
    op.create_index("ix_po_orders_updated_at", "po_purchase_orders", ["updated_at"])

    # ------------------------------------------------------------------
    # 2. po_purchase_order_revisions
    # ------------------------------------------------------------------
    op.create_table(
        "po_purchase_order_revisions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EDITABLE"),
        sa.Column("supplier_snapshot", _jsonb(), nullable=True),
        sa.Column("source_snapshot", _jsonb(), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("monetary_summary", _jsonb(), nullable=True),
        sa.Column("destination_snapshot", _jsonb(), nullable=True),
        sa.Column("terms_snapshot", _jsonb(), nullable=True),
        sa.Column("delivery_schedule_snapshot", _jsonb(), nullable=True),
        sa.Column("attachment_snapshot", _jsonb(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("created_from_revision_id", _uuid(), nullable=True),
        sa.Column("created_by", _uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_po_revisions_order_revision",
        "po_purchase_order_revisions",
        ["purchase_order_id", "revision_number"],
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_revisions_status",
            "po_purchase_order_revisions",
            "status IN ('EDITABLE','VALIDATED','PENDING_APPROVAL','APPROVED','FROZEN','SUPERSEDED','CANCELLED')",
        )
    op.create_index("ix_po_revisions_purchase_order_id", "po_purchase_order_revisions", ["purchase_order_id"])
    op.create_index("ix_po_revisions_status", "po_purchase_order_revisions", ["status"])

    # ------------------------------------------------------------------
    # 3. po_purchase_order_lines
    # ------------------------------------------------------------------
    op.create_table(
        "po_purchase_order_lines",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("source_allocation_id", _uuid(), nullable=True),
        sa.Column("evaluation_decision_line_id", _uuid(), nullable=True),
        sa.Column("quotation_response_line_id", _uuid(), nullable=True),
        sa.Column("product_id", _uuid(), nullable=True),
        sa.Column("product_version_id", _uuid(), nullable=True),
        sa.Column("sku_snapshot", sa.String(120), nullable=True),
        sa.Column("product_name_snapshot", sa.String(500), nullable=False),
        sa.Column("product_description_snapshot", sa.Text, nullable=True),
        sa.Column("specifications_snapshot", _jsonb(), nullable=True),
        sa.Column("supplier_product_reference", sa.String(120), nullable=True),
        sa.Column("ordered_quantity", sa.Numeric(28, 10), nullable=False),
        sa.Column("ordered_unit_id", _uuid(), nullable=True),
        sa.Column("ordered_unit_code", sa.String(20), nullable=False),
        sa.Column("base_quantity", sa.Numeric(28, 10), nullable=True),
        sa.Column("base_unit_id", _uuid(), nullable=True),
        sa.Column("base_unit_code", sa.String(20), nullable=True),
        sa.Column("unit_price", sa.Numeric(28, 10), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=True),
        sa.Column("discount_value", sa.Numeric(12, 8), nullable=True),
        sa.Column("discount_amount", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("tax_treatment", sa.String(40), nullable=True),
        sa.Column("tax_amount", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("freight_amount", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("other_charges_amount", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("line_subtotal", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(28, 10), nullable=False, server_default="0"),
        sa.Column("required_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("destination_warehouse_id", _uuid(), nullable=True),
        sa.Column("destination_snapshot", _jsonb(), nullable=True),
        sa.Column("delivery_terms", sa.Text, nullable=True),
        sa.Column("warranty_terms", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_unique_constraint(
        "uq_po_lines_revision_line",
        "po_purchase_order_lines",
        ["purchase_order_revision_id", "line_number"],
    )
    if is_pg:
        op.create_check_constraint("ck_po_lines_qty_positive", "po_purchase_order_lines", "ordered_quantity > 0")
        op.create_check_constraint("ck_po_lines_price_non_negative", "po_purchase_order_lines", "unit_price >= 0")
        op.create_check_constraint("ck_po_lines_discount_non_negative", "po_purchase_order_lines", "discount_amount >= 0")
        op.create_check_constraint("ck_po_lines_total_non_negative", "po_purchase_order_lines", "line_total >= 0")
        op.create_check_constraint(
            "ck_po_lines_status",
            "po_purchase_order_lines",
            "status IN ('ACTIVE','CANCELLED','SUPERSEDED')",
        )
    op.create_index("ix_po_lines_revision_id", "po_purchase_order_lines", ["purchase_order_revision_id"])
    op.create_index("ix_po_lines_product_id", "po_purchase_order_lines", ["product_id"])
    op.create_index("ix_po_lines_decision_line_id", "po_purchase_order_lines", ["evaluation_decision_line_id"])

    # ------------------------------------------------------------------
    # 4. po_source_allocations
    # ------------------------------------------------------------------
    op.create_table(
        "po_source_allocations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("organization_id", _uuid(), nullable=False),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purchase_order_line_id", _uuid(), nullable=True),
        sa.Column("evaluation_decision_id", _uuid(), nullable=False),
        sa.Column("evaluation_decision_line_id", _uuid(), nullable=False),
        sa.Column("quotation_response_id", _uuid(), nullable=True),
        sa.Column("quotation_response_line_id", _uuid(), nullable=True),
        sa.Column("requisition_line_id", _uuid(), nullable=True),
        sa.Column("supplier_business_partner_id", _uuid(), nullable=False),
        sa.Column("allocated_quantity", sa.Numeric(28, 10), nullable=False),
        sa.Column("allocated_unit_id", _uuid(), nullable=True),
        sa.Column("allocated_unit_code", sa.String(20), nullable=False),
        sa.Column("allocated_base_quantity", sa.Numeric(28, 10), nullable=True),
        sa.Column("source_unit_price", sa.Numeric(28, 10), nullable=False),
        sa.Column("source_currency_code", sa.String(3), nullable=False),
        sa.Column("source_line_total", sa.Numeric(28, 10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RESERVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint("ck_po_alloc_qty_positive", "po_source_allocations", "allocated_quantity > 0")
        op.create_check_constraint(
            "ck_po_alloc_status",
            "po_source_allocations",
            "status IN ('RESERVED','ACTIVE','CANCELLED','RELEASED')",
        )
    op.create_index("ix_po_alloc_decision_line_id", "po_source_allocations", ["evaluation_decision_line_id"])
    op.create_index("ix_po_alloc_po_line_id", "po_source_allocations", ["purchase_order_line_id"])
    op.create_index("ix_po_alloc_status", "po_source_allocations", ["status"])

    # ------------------------------------------------------------------
    # 5. po_source_variances
    # ------------------------------------------------------------------
    op.create_table(
        "po_source_variances",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision_id", _uuid(), nullable=True),
        sa.Column("line_id", _uuid(), nullable=True),
        sa.Column("variance_type", sa.String(40), nullable=False),
        sa.Column("source_value", _jsonb(), nullable=True),
        sa.Column("proposed_value", _jsonb(), nullable=True),
        sa.Column("monetary_impact", sa.Numeric(28, 10), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("evidence_file_id", _uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DETECTED"),
        sa.Column("requested_by", _uuid(), nullable=False),
        sa.Column("reviewed_by", _uuid(), nullable=True),
        sa.Column("approved_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_variance_type",
            "po_source_variances",
            "variance_type IN ('QUANTITY_REDUCTION','DELIVERY_DATE_ADJUSTMENT','DESTINATION_ADJUSTMENT',"
            "'TAX_CLARIFICATION','FREIGHT_CLARIFICATION','ROUNDING_ADJUSTMENT',"
            "'COMMERCIAL_TERM_CLARIFICATION','PRICE_EXCEPTION','OTHER')",
        )
        op.create_check_constraint(
            "ck_po_variance_status",
            "po_source_variances",
            "status IN ('DETECTED','JUSTIFIED','APPROVED','REJECTED','SUPERSEDED')",
        )
    op.create_index("ix_po_variance_purchase_order_id", "po_source_variances", ["purchase_order_id"])

    # ------------------------------------------------------------------
    # 6. po_tax_components
    # ------------------------------------------------------------------
    op.create_table(
        "po_tax_components",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("line_id", _uuid(), nullable=True),
        sa.Column("tax_code", sa.String(20), nullable=False),
        sa.Column("tax_name", sa.String(100), nullable=False),
        sa.Column("tax_category", sa.String(40), nullable=False),
        sa.Column("tax_rate", sa.Numeric(12, 8), nullable=False),
        sa.Column("taxable_base", sa.Numeric(28, 10), nullable=False),
        sa.Column("tax_amount", sa.Numeric(28, 10), nullable=False),
        sa.Column("included_in_price", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source_type", sa.String(40), nullable=True),
        sa.Column("source_reference", sa.String(120), nullable=True),
        sa.Column("calculation_method", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint("ck_po_tax_rate_non_negative", "po_tax_components", "tax_rate >= 0")
        op.create_check_constraint("ck_po_tax_amount_non_negative", "po_tax_components", "tax_amount >= 0")
        op.create_check_constraint(
            "ck_po_tax_category",
            "po_tax_components",
            "tax_category IN ('GENERAL_SALES_TAX','WITHHOLDING_REFERENCE','PERCEPTION_REFERENCE','EXEMPT','UNAFFECTED','OTHER')",
        )
    op.create_index("ix_po_tax_revision_id", "po_tax_components", ["revision_id"])

    # ------------------------------------------------------------------
    # 7. po_charges
    # ------------------------------------------------------------------
    op.create_table(
        "po_charges",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("line_id", _uuid(), nullable=True),
        sa.Column("charge_type", sa.String(30), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("amount", sa.Numeric(28, 10), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("taxable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("tax_code", sa.String(20), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=True),
        sa.Column("source_reference", sa.String(120), nullable=True),
        sa.Column("created_by", _uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint("ck_po_charge_amount_non_negative", "po_charges", "amount >= 0")
        op.create_check_constraint(
            "ck_po_charge_type",
            "po_charges",
            "charge_type IN ('FREIGHT','INSURANCE','PACKAGING','HANDLING','INSTALLATION','SERVICE','OTHER')",
        )
    op.create_index("ix_po_charge_revision_id", "po_charges", ["revision_id"])

    # ------------------------------------------------------------------
    # 8. po_payment_terms
    # ------------------------------------------------------------------
    op.create_table(
        "po_payment_terms",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("term_type", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(60), nullable=True),
        sa.Column("credit_days", sa.Integer, nullable=True),
        sa.Column("advance_percentage", sa.Numeric(12, 8), nullable=True),
        sa.Column("milestone_schedule", _jsonb(), nullable=True),
        sa.Column("payment_reference", sa.String(120), nullable=True),
        sa.Column("bank_instruction_reference", sa.String(120), nullable=True),
        sa.Column("retention_percentage", sa.Numeric(12, 8), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(40), nullable=True),
        sa.Column("source_reference", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_pt_term_type",
            "po_payment_terms",
            "term_type IN ('CASH','CREDIT','ADVANCE_AND_BALANCE','MILESTONES','AGAINST_DELIVERY','AGAINST_ACCEPTANCE','OTHER')",
        )
        op.create_check_constraint(
            "ck_po_pt_advance_pct",
            "po_payment_terms",
            "advance_percentage IS NULL OR (advance_percentage >= 0 AND advance_percentage <= 100)",
        )
        op.create_check_constraint(
            "ck_po_pt_retention_pct",
            "po_payment_terms",
            "retention_percentage IS NULL OR (retention_percentage >= 0 AND retention_percentage <= 100)",
        )
    op.create_index("ix_po_pt_revision_id", "po_payment_terms", ["revision_id"])

    # ------------------------------------------------------------------
    # 9. po_delivery_terms
    # ------------------------------------------------------------------
    op.create_table(
        "po_delivery_terms",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("delivery_mode", sa.String(40), nullable=True),
        sa.Column("freight_responsibility", sa.String(40), nullable=True),
        sa.Column("delivery_location_type", sa.String(40), nullable=True),
        sa.Column("destination_warehouse_id", _uuid(), nullable=True),
        sa.Column("destination_address_snapshot", _jsonb(), nullable=True),
        sa.Column("partial_delivery_allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("early_delivery_allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("late_delivery_tolerance_days", sa.Integer, nullable=True),
        sa.Column("receiving_hours", sa.String(100), nullable=True),
        sa.Column("appointment_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("packaging_requirements", sa.Text, nullable=True),
        sa.Column("labeling_requirements", sa.Text, nullable=True),
        sa.Column("documentation_requirements", sa.Text, nullable=True),
        sa.Column("incoterm_code", sa.String(10), nullable=True),
        sa.Column("transfer_of_risk_reference", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_po_dt_revision_id", "po_delivery_terms", ["revision_id"])

    # ------------------------------------------------------------------
    # 10. po_delivery_schedules
    # ------------------------------------------------------------------
    op.create_table(
        "po_delivery_schedules",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_revision_id", _uuid(), sa.ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("schedule_number", sa.Integer, nullable=False),
        sa.Column("planned_delivery_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_delivery_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_delivery_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(60), nullable=False, server_default="UTC"),
        sa.Column("destination_warehouse_id", _uuid(), nullable=True),
        sa.Column("destination_address_snapshot", _jsonb(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PLANNED"),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_po_schedules_revision_number",
        "po_delivery_schedules",
        ["purchase_order_revision_id", "schedule_number"],
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_schedule_status",
            "po_delivery_schedules",
            "status IN ('PLANNED','CONFIRMED','RESCHEDULED','CANCELLED','COMPLETED_FUTURE')",
        )
    op.create_index("ix_po_sched_revision_id", "po_delivery_schedules", ["purchase_order_revision_id"])
    op.create_index("ix_po_sched_planned_date", "po_delivery_schedules", ["planned_delivery_date"])
    op.create_index("ix_po_sched_dest_warehouse_id", "po_delivery_schedules", ["destination_warehouse_id"])

    # ------------------------------------------------------------------
    # 11. po_delivery_schedule_lines
    # ------------------------------------------------------------------
    op.create_table(
        "po_delivery_schedule_lines",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("delivery_schedule_id", _uuid(), sa.ForeignKey("po_delivery_schedules.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purchase_order_line_id", _uuid(), nullable=False),
        sa.Column("scheduled_quantity", sa.Numeric(28, 10), nullable=False),
        sa.Column("scheduled_unit_id", _uuid(), nullable=True),
        sa.Column("scheduled_unit_code", sa.String(20), nullable=False),
        sa.Column("scheduled_base_quantity", sa.Numeric(28, 10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint("ck_po_sched_line_qty_positive", "po_delivery_schedule_lines", "scheduled_quantity > 0")
    op.create_index("ix_po_sched_line_schedule_id", "po_delivery_schedule_lines", ["delivery_schedule_id"])
    op.create_index("ix_po_sched_line_po_line_id", "po_delivery_schedule_lines", ["purchase_order_line_id"])

    # ------------------------------------------------------------------
    # 12. po_approval_decisions
    # ------------------------------------------------------------------
    op.create_table(
        "po_approval_decisions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision_id", _uuid(), nullable=False),
        sa.Column("policy_code", sa.String(80), nullable=False),
        sa.Column("policy_version", sa.String(20), nullable=False),
        sa.Column("decision_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("decided_by", _uuid(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("conditions", _jsonb(), nullable=True),
        sa.Column("step_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_final", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("supersedes_decision_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_approval_decision_type",
            "po_approval_decisions",
            "decision_type IN ('APPROVE','REJECT','RETURN_FOR_CHANGES','CANCEL_APPROVAL')",
        )
        op.create_check_constraint(
            "ck_po_approval_status_val",
            "po_approval_decisions",
            "status IN ('ACTIVE','SUPERSEDED','CANCELLED')",
        )
    op.create_index("ix_po_approval_purchase_order_id", "po_approval_decisions", ["purchase_order_id"])
    op.create_index("ix_po_approval_revision_id", "po_approval_decisions", ["revision_id"])

    # ------------------------------------------------------------------
    # 13. po_dispatches
    # ------------------------------------------------------------------
    op.create_table(
        "po_dispatches",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_instance_id", _uuid(), nullable=True),
        sa.Column("supplier_id", _uuid(), nullable=False),
        sa.Column("contact_snapshot", _jsonb(), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="QUEUED"),
        sa.Column("provider_message_id", sa.String(200), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(60), nullable=True),
        sa.Column("failure_summary", sa.Text, nullable=True),
        sa.Column("manually_delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manually_delivered_by", _uuid(), nullable=True),
        sa.Column("manual_delivery_reference", sa.String(200), nullable=True),
        sa.Column("acknowledgement_requested", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", _uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_dispatch_channel",
            "po_dispatches",
            "channel IN ('EMAIL','SECURE_PORTAL','EMAIL_AND_PORTAL','MANUAL','API_AUTHORIZED')",
        )
        op.create_check_constraint(
            "ck_po_dispatch_status",
            "po_dispatches",
            "status IN ('QUEUED','SENDING','SENT','DELIVERED','FAILED','MANUALLY_DELIVERED','CANCELLED')",
        )
    op.create_index("ix_po_dispatch_purchase_order_id", "po_dispatches", ["purchase_order_id"])
    op.create_index("ix_po_dispatch_status", "po_dispatches", ["status"])
    op.create_index("ix_po_dispatch_provider_message_id", "po_dispatches", ["provider_message_id"])

    # ------------------------------------------------------------------
    # 14. po_delivery_attempts
    # ------------------------------------------------------------------
    op.create_table(
        "po_delivery_attempts",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("dispatch_id", _uuid(), sa.ForeignKey("po_dispatches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(60), nullable=True),
        sa.Column("provider_message_id", sa.String(200), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="QUEUED"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(60), nullable=True),
        sa.Column("failure_summary", sa.Text, nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_attempt_status",
            "po_delivery_attempts",
            "status IN ('QUEUED','SENDING','ACCEPTED_BY_PROVIDER','DELIVERED','BOUNCED','REJECTED','FAILED','CANCELLED','UNKNOWN')",
        )
    op.create_index("ix_po_attempt_dispatch_id", "po_delivery_attempts", ["dispatch_id"])

    # ------------------------------------------------------------------
    # 15. po_acknowledgements
    # ------------------------------------------------------------------
    op.create_table(
        "po_acknowledgements",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dispatch_id", _uuid(), nullable=True),
        sa.Column("acknowledgement_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RECEIVED"),
        sa.Column("supplier_reference", sa.String(200), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledgement_channel", sa.String(30), nullable=False),
        sa.Column("acknowledged_by_name", sa.String(200), nullable=True),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("file_reference_id", _uuid(), nullable=True),
        sa.Column("received_by_user_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_ack_type",
            "po_acknowledgements",
            "acknowledgement_type IN ('RECEIPT_CONFIRMATION','FULL_ACCEPTANCE','ACCEPTANCE_WITH_OBSERVATIONS','REJECTION','REQUEST_FOR_CLARIFICATION')",
        )
        op.create_check_constraint(
            "ck_po_ack_status",
            "po_acknowledgements",
            "status IN ('RECEIVED','VALIDATED','REJECTED','SUPERSEDED')",
        )
    op.create_index("ix_po_ack_purchase_order_id", "po_acknowledgements", ["purchase_order_id"])

    # ------------------------------------------------------------------
    # 16. po_amendments
    # ------------------------------------------------------------------
    op.create_table(
        "po_amendments",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("purchase_order_id", _uuid(), sa.ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amendment_number", sa.Integer, nullable=False),
        sa.Column("amendment_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("previous_snapshot_hash", sa.String(64), nullable=True),
        sa.Column("proposed_changes", _jsonb(), nullable=True),
        sa.Column("monetary_impact", sa.Numeric(28, 10), nullable=True),
        sa.Column("schedule_impact", _jsonb(), nullable=True),
        sa.Column("requires_supplier_acceptance", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("approval_status", sa.String(30), nullable=True),
        sa.Column("document_instance_id", _uuid(), nullable=True),
        sa.Column("created_by", _uuid(), nullable=False),
        sa.Column("approved_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_po_amendments_order_number",
        "po_amendments",
        ["purchase_order_id", "amendment_number"],
    )
    if is_pg:
        op.create_check_constraint(
            "ck_po_amendment_type",
            "po_amendments",
            "amendment_type IN ('QUANTITY_REDUCTION','DELIVERY_RESCHEDULE','DESTINATION_CHANGE',"
            "'TERM_CHANGE','PRICE_CHANGE_WITH_NEW_DECISION','CANCELLATION','OTHER')",
        )
        op.create_check_constraint(
            "ck_po_amendment_status",
            "po_amendments",
            "status IN ('DRAFT','PENDING_APPROVAL','APPROVED','ISSUED','CANCELLED','REJECTED')",
        )
    op.create_index("ix_po_amendment_purchase_order_id", "po_amendments", ["purchase_order_id"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("po_amendments")
    op.drop_table("po_acknowledgements")
    op.drop_table("po_delivery_attempts")
    op.drop_table("po_dispatches")
    op.drop_table("po_approval_decisions")
    op.drop_table("po_delivery_schedule_lines")
    op.drop_table("po_delivery_schedules")
    op.drop_table("po_delivery_terms")
    op.drop_table("po_payment_terms")
    op.drop_table("po_charges")
    op.drop_table("po_tax_components")
    op.drop_table("po_source_variances")
    op.drop_table("po_source_allocations")
    op.drop_table("po_purchase_order_lines")
    op.drop_table("po_purchase_order_revisions")
    op.drop_table("po_purchase_orders")
