"""Repair databases stamped past Phase 029 without the driver tables.

Revision ID: ad390210039dr
Revises: ac390110039dc
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ad390210039dr"
down_revision: Union[str, Sequence[str], None] = "ac390110039dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DRIVER_TABLES = {
    "drivers",
    "driver_versions",
    "driver_identity_documents",
    "driver_licenses",
    "driver_license_categories",
    "driver_license_category_assignments",
    "driver_license_restrictions",
    "driver_license_vehicle_type_rules",
    "driver_carrier_assignments",
    "driver_contacts",
    "driver_emergency_contacts",
    "driver_photos",
    "driver_documents",
    "driver_document_requirements",
    "driver_operational_restrictions",
    "driver_user_account_links",
}


def upgrade() -> None:
    present = _DRIVER_TABLES.intersection(sa.inspect(op.get_bind()).get_table_names())
    if present == _DRIVER_TABLES:
        return
    if present:
        missing = ", ".join(sorted(_DRIVER_TABLES - present))
        raise RuntimeError(f"Partial Phase 029 driver schema; missing: {missing}")

    migration_path = Path(__file__).with_name("t310110029dc_phase_029_drivers.py")
    spec = importlib.util.spec_from_file_location("phase_029_driver_schema_repair", migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the Phase 029 driver migration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.upgrade()


def downgrade() -> None:
    # These tables may contain pre-existing production data. A repair downgrade
    # must never delete them; the original Phase 029 downgrade remains canonical.
    pass
