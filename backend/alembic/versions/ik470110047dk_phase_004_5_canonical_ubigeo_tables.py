"""Phase 004.5 — Canonical UBIGEO tables, branch location normalization and coordinates constraints.

Revision ID: ik470110047dk
Revises: hj460110046dk
Create Date: 2026-08-17 02:30:00.000000

Creates:
  1. geo_departments (25 departments of Peru)
  2. geo_provinces (196 provinces of Peru)
  3. geo_districts (1893 canonical districts of Peru with 6-digit UBIGEO)

Alters:
  - logistics_branches: adds ubigeo_code FK to geo_districts.code (SET NULL)
  - logistics_branches: adds check constraints for valid coordinate ranges
  - Enables Row Level Security (RLS) on all 3 new geo tables
  - Populates canonical INEI/RENIEC UBIGEO dataset
"""

import json
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ik470110047dk"
down_revision: Union[str, None] = "hj460110046dk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. geo_departments
    op.create_table(
        "geo_departments",
        sa.Column("code", sa.String(length=2), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
    )

    # 2. geo_provinces
    op.create_table(
        "geo_provinces",
        sa.Column("code", sa.String(length=4), primary_key=True),
        sa.Column(
            "department_code",
            sa.String(length=2),
            sa.ForeignKey("geo_departments.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_geo_provinces_department_code", "geo_provinces", ["department_code"])

    # 3. geo_districts
    op.create_table(
        "geo_districts",
        sa.Column("code", sa.String(length=6), primary_key=True),
        sa.Column(
            "province_code",
            sa.String(length=4),
            sa.ForeignKey("geo_provinces.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_code",
            sa.String(length=2),
            sa.ForeignKey("geo_departments.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_geo_districts_province_code", "geo_districts", ["province_code"])
    op.create_index("ix_geo_districts_department_code", "geo_districts", ["department_code"])

    # 4. Alter logistics_branches
    op.add_column(
        "logistics_branches",
        sa.Column("ubigeo_code", sa.String(length=6), nullable=True),
    )
    op.create_foreign_key(
        "fk_branches_ubigeo_code",
        "logistics_branches",
        "geo_districts",
        ["ubigeo_code"],
        ["code"],
        ondelete="SET NULL",
    )
    op.create_index("ix_logistics_branches_ubigeo_code", "logistics_branches", ["ubigeo_code"])

    # 5. Coordinate CHECK constraints on PostgreSQL/SQLite
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        op.execute(
            "ALTER TABLE logistics_branches ADD CONSTRAINT chk_branches_latitude "
            "CHECK (latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0));"
        )
        op.execute(
            "ALTER TABLE logistics_branches ADD CONSTRAINT chk_branches_longitude "
            "CHECK (longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0));"
        )

        # 6. Enable RLS on new tables in PostgreSQL
        op.execute("ALTER TABLE geo_departments ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE geo_provinces ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE geo_districts ENABLE ROW LEVEL SECURITY;")

    # 7. Seed canonical UBIGEO dataset
    json_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "modules", "logistics", "geography", "ubigeo_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dept_table = sa.table("geo_departments", sa.column("code"), sa.column("name"))
        prov_table = sa.table("geo_provinces", sa.column("code"), sa.column("department_code"), sa.column("name"))
        dist_table = sa.table("geo_districts", sa.column("code"), sa.column("province_code"), sa.column("department_code"), sa.column("name"))

        if data.get("departments"):
            op.bulk_insert(dept_table, data["departments"])
        if data.get("provinces"):
            op.bulk_insert(prov_table, data["provinces"])
        if data.get("districts"):
            op.bulk_insert(dist_table, data["districts"])


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("ALTER TABLE logistics_branches DROP CONSTRAINT IF EXISTS chk_branches_latitude;")
        op.execute("ALTER TABLE logistics_branches DROP CONSTRAINT IF EXISTS chk_branches_longitude;")

    op.drop_constraint("fk_branches_ubigeo_code", "logistics_branches", type_="foreignkey")
    op.drop_index("ix_logistics_branches_ubigeo_code", table_name="logistics_branches")
    op.drop_column("logistics_branches", "ubigeo_code")

    op.drop_table("geo_districts")
    op.drop_table("geo_provinces")
    op.drop_table("geo_departments")
