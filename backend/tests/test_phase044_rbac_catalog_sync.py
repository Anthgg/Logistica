"""Regression coverage for the Phase 044 RBAC catalog synchronization."""

import importlib.util
from pathlib import Path

from app.modules.logistics.rbac.permission_catalog import (
    PHASE_044_PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)

REQUIRED_PERMISSION = "logistics.inventory_ledger.read"


def test_phase044_read_permission_is_registered_for_logistics_admin() -> None:
    phase_codes = {str(permission["code"]) for permission in PHASE_044_PERMISSIONS}

    assert REQUIRED_PERMISSION in phase_codes
    assert REQUIRED_PERMISSION in ROLE_PERMISSION_MATRIX["LOGISTICS_ADMIN"]


def test_phase044_rbac_sync_is_the_alembic_head() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "gi440310044rb_sync_phase044_rbac_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("phase044_rbac_sync", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "gi440310044rb"
    assert migration.down_revision == "gh440210044mg"
    assert migration._stable_id("permission", REQUIRED_PERMISSION) == migration._stable_id(
        "permission", REQUIRED_PERMISSION
    )


def test_phase044_ledger_migration_moves_legacy_index_namespace() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "gg440110044dc_phase_044_inventory_ledger.py"
    )
    spec = importlib.util.spec_from_file_location("phase044_ledger", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration._legacy_index_name("ix_inventory_movements_movement_type") == (
        "ix_inventory_movements_legacy_movement_type"
    )
    assert migration._legacy_index_name("inventory_movements_pkey") is None
