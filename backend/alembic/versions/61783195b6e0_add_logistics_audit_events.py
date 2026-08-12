"""add logistics audit events

Revision ID: 61783195b6e0
Revises: af2daf23238c
Create Date: 2026-07-26 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "61783195b6e0"
down_revision: Union[str, None] = "af2daf23238c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_code", sa.String(150), nullable=False, index=True),
        sa.Column("event_category", sa.String(50), nullable=False, index=True),
        sa.Column("event_version", sa.String(20), nullable=False, server_default="'1.0'"),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("actor_type", sa.String(30), nullable=False, server_default="'user'"),
        sa.Column("actor_display_name_snapshot", sa.String(200), nullable=True),
        sa.Column("actor_role_codes_snapshot", sa.Text, nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("authentication_level", sa.String(30), nullable=True),
        sa.Column("risk_score", sa.Float, nullable=True),
        sa.Column("step_up_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("step_up_result", sa.String(30), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("request_id", sa.String(100), nullable=True, index=True),
        sa.Column("correlation_id", sa.String(100), nullable=True, index=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("origin", sa.String(500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True, server_default=sa.text("now()")),
        sa.Column("resource_type", sa.String(100), nullable=True, index=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("resource_code", sa.String(100), nullable=True),
        sa.Column("parent_resource_type", sa.String(100), nullable=True),
        sa.Column("parent_resource_id", sa.String(255), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("result", sa.String(20), nullable=False, server_default="'success'", index=True),
        sa.Column("reason_code", sa.String(50), nullable=True),
        sa.Column("reason_text", sa.String(500), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="'info'", index=True),
        sa.Column("previous_data", postgresql.JSONB, nullable=True),
        sa.Column("new_data", postgresql.JSONB, nullable=True),
        sa.Column("changed_fields", postgresql.JSONB, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("source_module", sa.String(50), nullable=True),
        sa.Column("source_service", sa.String(100), nullable=True),
        sa.Column("event_hash", sa.String(128), nullable=True),
        sa.Column("hash_algorithm", sa.String(20), nullable=False, server_default="'sha256'"),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="'1.0'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    # Composite index for resource lookups
    op.create_index("ix_audit_events_resource", "logistics_audit_events", ["resource_type", "resource_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_resource", "logistics_audit_events")
    op.drop_table("logistics_audit_events")