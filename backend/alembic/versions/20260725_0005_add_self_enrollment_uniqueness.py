"""Prevent duplicate active participant profiles for one user.

Revision ID: 20260725_0005
Revises: 20260725_0004
Create Date: 2026-07-25 22:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260725_0005"
down_revision: str | None = "20260725_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_research_participants_active_linked_user",
        "research_participants",
        ["linked_user_id"],
        unique=True,
        postgresql_where=sa.text(
            "linked_user_id IS NOT NULL AND is_active = true"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_research_participants_active_linked_user",
        table_name="research_participants",
    )
