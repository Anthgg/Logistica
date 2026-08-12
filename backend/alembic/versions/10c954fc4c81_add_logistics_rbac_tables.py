"""add logistics rbac tables

Revision ID: 10c954fc4c81
Revises: a2f27fd9a6c0
Create Date: 2026-07-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "10c954fc4c81"
down_revision: Union[str, None] = "a2f27fd9a6c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("role_type", sa.String(20), nullable=False, server_default="'system'", index=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "logistics_role_scope_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("allowed_scope_type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("role_id", "allowed_scope_type", name="uq_role_scope_type"),
    )

    op.create_table(
        "logistics_role_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_roles.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("scope_type", sa.String(20), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "user_id", "role_id", "scope_type",
            "organization_id", "branch_id", "warehouse_id", "status",
            name="uq_assignment_active_unique",
        ),
    )

    op.create_table(
        "logistics_role_conflict_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_a_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role_b_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("conflict_type", sa.String(30), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("role_a_id", "role_b_id", name="uq_role_conflict_pair"),
    )


def downgrade() -> None:
    op.drop_table("logistics_role_conflict_rules")
    op.drop_table("logistics_role_assignments")
    op.drop_table("logistics_role_scope_rules")
    op.drop_table("logistics_roles")