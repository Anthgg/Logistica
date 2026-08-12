"""add step up tables

Revision ID: f0424c5e9d46
Revises: 61783195b6e0
Create Date: 2026-07-26 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f0424c5e9d46"
down_revision: Union[str, None] = "61783195b6e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_step_up_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("permission_code", sa.String(100), nullable=False, index=True),
        sa.Column("action_code", sa.String(100), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'", index=True),
        sa.Column("required_factors", postgresql.JSONB, nullable=False),
        sa.Column("reason_codes", postgresql.JSONB, server_default=sa.text("'[]'")),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("risk_score", sa.Float, nullable=True),
        sa.Column("reason_text", sa.String(500), nullable=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("correlation_id", sa.String(100), nullable=True, index=True),
        sa.Column("policy_version", sa.String(20), nullable=False, server_default="'1.0.0'"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, index=True, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "logistics_step_up_proofs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("logistics_step_up_challenges.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("permission_code", sa.String(100), nullable=False, index=True),
        sa.Column("action_code", sa.String(100), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True),
        sa.Column("one_time", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("proof_hash", sa.String(128), nullable=False),
        sa.Column("policy_version", sa.String(20), nullable=False, server_default="'1.0.0'"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("logistics_step_up_proofs")
    op.drop_table("logistics_step_up_challenges")