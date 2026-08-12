"""add logistics permissions tables

Revision ID: af2daf23238c
Revises: 10c954fc4c81
Create Date: 2026-07-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "af2daf23238c"
down_revision: Union[str, None] = "10c954fc4c81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("resource", sa.String(50), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="'low'", index=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_reason", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_step_up", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "logistics_role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_permissions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("effect", sa.String(10), nullable=False, server_default="'allow'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "logistics_permission_scope_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_permissions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("allowed_scope_type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("permission_id", "allowed_scope_type", name="uq_perm_scope_type"),
    )


def downgrade() -> None:
    op.drop_table("logistics_permission_scope_rules")
    op.drop_table("logistics_role_permissions")
    op.drop_table("logistics_permissions")