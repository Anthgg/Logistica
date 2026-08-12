"""Add purchase-order lifecycle tables.

Revision ID: t310110029dc
Revises: s310110028dc
Create Date: 2026-07-28 20:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "t290110029po"
down_revision: Union[str, None] = "s310110028dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_partners.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("order_number", sa.String(40), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PEN"),
        sa.Column(
            "subtotal_amount",
            sa.Numeric(18, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(18, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(18, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("annulled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("annulled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("annulment_reason", sa.Text(), nullable=True),
        sa.Column(
            "row_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "order_number",
            name="uq_purchase_orders_org_number",
        ),
    )
    op.create_index(
        "ix_purchase_orders_organization_id",
        "purchase_orders",
        ["organization_id"],
    )
    op.create_index(
        "ix_purchase_orders_supplier_id",
        "purchase_orders",
        ["supplier_id"],
    )
    op.create_index(
        "ix_purchase_orders_status",
        "purchase_orders",
        ["status"],
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "purchase_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("unit_code", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 6), nullable=False),
        sa.Column(
            "tax_rate",
            sa.Numeric(7, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("subtotal_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "purchase_order_id",
            "line_number",
            name="uq_purchase_order_lines_order_number",
        ),
    )
    op.create_index(
        "ix_purchase_order_lines_purchase_order_id",
        "purchase_order_lines",
        ["purchase_order_id"],
    )
    op.create_index(
        "ix_purchase_order_lines_product_id",
        "purchase_order_lines",
        ["product_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_purchase_order_lines_product_id",
        table_name="purchase_order_lines",
    )
    op.drop_index(
        "ix_purchase_order_lines_purchase_order_id",
        table_name="purchase_order_lines",
    )
    op.drop_table("purchase_order_lines")
    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_organization_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
