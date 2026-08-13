"""gh450310045pu — Phase 045: Add partial unique active index to inventory_position_balances.

Ensures at most ONE active projection (is_active_projection = TRUE) exists per
(organization_id, inventory_position_id), while allowing multiple inactive staging
projections (is_active_projection = FALSE) during rebuilds.

Revision ID: gh450310045pu
Revises: gg450210045sw
Create Date: 2026-08-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "gh450310045pu"
down_revision = "gg450210045sw"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_ipb_active_position",
        "inventory_position_balances",
        ["organization_id", "inventory_position_id"],
        unique=True,
        postgresql_where=sa.text("is_active_projection = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("uq_ipb_active_position", table_name="inventory_position_balances")
