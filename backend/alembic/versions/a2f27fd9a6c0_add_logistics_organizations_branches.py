"""add logistics organizations, branches, warehouse branch_id

Revision ID: a2f27fd9a6c0
Revises: 20260725_0006
Create Date: 2026-07-26 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a2f27fd9a6c0"
down_revision: Union[str, None] = "20260725_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create logistics_organizations ---
    op.create_table(
        "logistics_organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="'America/Lima'"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- Create logistics_branches ---
    op.create_table(
        "logistics_branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="'America/Lima'"),
        sa.Column("address_text", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "code", name="uq_branches_org_code"),
    )

    # --- Add branch_id and warehouse_type to existing warehouses ---
    op.add_column("warehouses", sa.Column("branch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=True, index=True))
    op.add_column("warehouses", sa.Column("warehouse_type", sa.String(30),
                  nullable=False, server_default="'general'"))
    op.add_column("warehouses", sa.Column("is_default", sa.Boolean(),
                  nullable=False, server_default=sa.text("false")))
    op.create_unique_constraint("uq_warehouses_branch_code", "warehouses", ["branch_id", "code"])


def downgrade() -> None:
    op.drop_constraint("uq_warehouses_branch_code", "warehouses", type_="unique")
    op.drop_column("warehouses", "is_default")
    op.drop_column("warehouses", "warehouse_type")
    op.drop_column("warehouses", "branch_id")
    op.drop_table("logistics_branches")
    op.drop_table("logistics_organizations")