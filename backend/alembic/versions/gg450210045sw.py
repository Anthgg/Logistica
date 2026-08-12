"""gg450210045sw — Phase 045: Add rebuild staging support to inventory_position_balances.

Adds:
- rebuild_job_id (UUID, nullable) → references inventory_balance_rebuild_jobs(id)
- is_active_projection (BOOLEAN, NOT NULL, DEFAULT TRUE)

These columns enable the atomic swap mechanism for the Rebuild service:
- G1 (active): is_active_projection=TRUE, rebuild_job_id=NULL
- G2 (staging): is_active_projection=FALSE, rebuild_job_id=<job_id>
- After swap: G2.is_active_projection=TRUE, G1.is_active_projection=FALSE

Revision ID: gg450210045sw
Revises: hh450110045dc
Create Date: 2026-08-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "gg450210045sw"
down_revision = "hh450110045dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rebuild_job_id — nullable FK to inventory_balance_rebuild_jobs
    op.add_column(
        "inventory_position_balances",
        sa.Column(
            "rebuild_job_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_ipb_rebuild_job_id",
        "inventory_position_balances",
        "inventory_balance_rebuild_jobs",
        ["rebuild_job_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add is_active_projection — active generation flag for atomic swap
    op.add_column(
        "inventory_position_balances",
        sa.Column(
            "is_active_projection",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
    )

    # Add index for efficient reads of active projection
    op.create_index(
        "ix_ipb_active_projection",
        "inventory_position_balances",
        ["organization_id", "is_active_projection"],
    )

    # Expand materialization_key from String(128) to String(255) to support long keys
    op.alter_column(
        "inventory_balance_deltas",
        "materialization_key",
        type_=sa.String(255),
        existing_type=sa.String(128),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ipb_active_projection", table_name="inventory_position_balances")
    op.drop_constraint(
        "fk_ipb_rebuild_job_id", "inventory_position_balances", type_="foreignkey"
    )
    op.drop_column("inventory_position_balances", "is_active_projection")
    op.drop_column("inventory_position_balances", "rebuild_job_id")
