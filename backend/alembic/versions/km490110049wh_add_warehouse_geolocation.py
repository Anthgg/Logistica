"""Add inherited/custom geolocation to warehouses.

Existing rows remain inherited and keep their own coordinates NULL.  The
effective point is resolved from the related branch at read time, so a branch
move is immediately reflected without copying stale coordinates.

Revision ID: km490110049wh
Revises: jl480110048dk
"""

import sqlalchemy as sa

from alembic import op

revision = "km490110049wh"
down_revision = "jl480110048dk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "warehouses",
        sa.Column(
            "uses_branch_location",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "warehouses",
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
    )
    op.add_column(
        "warehouses",
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
    )

    op.create_check_constraint(
        "chk_warehouses_latitude",
        "warehouses",
        "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
    )
    op.create_check_constraint(
        "chk_warehouses_longitude",
        "warehouses",
        "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
    )
    op.create_check_constraint(
        "chk_warehouses_location_mode",
        "warehouses",
        "(uses_branch_location AND latitude IS NULL AND longitude IS NULL) "
        "OR (NOT uses_branch_location AND latitude IS NOT NULL AND longitude IS NOT NULL)",
    )
    # Supabase already enables RLS on this productive table. Repeating the
    # idempotent ALTER keeps fresh Alembic-built databases aligned without
    # replacing or broadening any existing policy.
    op.execute("ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_constraint("chk_warehouses_location_mode", "warehouses", type_="check")
    op.drop_constraint("chk_warehouses_longitude", "warehouses", type_="check")
    op.drop_constraint("chk_warehouses_latitude", "warehouses", type_="check")
    op.drop_column("warehouses", "longitude")
    op.drop_column("warehouses", "latitude")
    op.drop_column("warehouses", "uses_branch_location")
