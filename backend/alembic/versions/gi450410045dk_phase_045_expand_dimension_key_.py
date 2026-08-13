"""phase_045_expand_dimension_key_varchar255

GAP 4 FIX (Phase 045 Hardening):
Expand inventory_position_balances.dimension_key from VARCHAR(64) to VARCHAR(255)
to match the canonical F044 source: inventory_positions.dimension_key VARCHAR(255).

Truncating dimension_key to 64 chars is PROHIBITED because two distinct dimension_keys
sharing the same first 64 characters would appear identical, causing silent collisions.

Revision ID: gi450410045dk
Revises: gh450310045pu
Create Date: 2026-08-12 21:47:13.081532

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "gi450410045dk"
down_revision: str | Sequence[str] | None = "gh450310045pu"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Expand dimension_key column from VARCHAR(64) to VARCHAR(255).

    inventory_position_balances.dimension_key must match the canonical
    inventory_positions.dimension_key (VARCHAR 255) from Phase 044.
    """
    op.alter_column(
        "inventory_position_balances",
        "dimension_key",
        existing_type=sa.String(64),
        type_=sa.String(255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Shrink dimension_key column back to VARCHAR(64).

    WARNING: Data truncation may occur if any rows have dimension_key longer than 64 chars.
    """
    op.alter_column(
        "inventory_position_balances",
        "dimension_key",
        existing_type=sa.String(255),
        type_=sa.String(64),
        existing_nullable=False,
    )
