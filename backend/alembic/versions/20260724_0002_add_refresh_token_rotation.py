"""add refresh token rotation

Revision ID: 20260724_0002
Revises: 20260723_0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260724_0002"
down_revision: str | None = "20260723_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions", sa.Column("refresh_token_hash", sa.String(255), nullable=True)
    )
    op.add_column(
        "sessions",
        sa.Column("previous_refresh_token_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "sessions",
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_sessions_refresh_token_hash",
        "sessions",
        ["refresh_token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_sessions_previous_refresh_token_hash",
        "sessions",
        ["previous_refresh_token_hash"],
    )
    op.create_index(
        "ix_sessions_refresh_expires_at",
        "sessions",
        ["refresh_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_refresh_expires_at", table_name="sessions")
    op.drop_index("ix_sessions_previous_refresh_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_refresh_token_hash", table_name="sessions")
    op.drop_column("sessions", "refresh_expires_at")
    op.drop_column("sessions", "previous_refresh_token_hash")
    op.drop_column("sessions", "refresh_token_hash")
