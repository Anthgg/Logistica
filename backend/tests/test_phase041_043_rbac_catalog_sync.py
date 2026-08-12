"""Regression coverage for the Phase 041-043 RBAC catalog synchronization."""

import importlib.util
from pathlib import Path

from app.modules.logistics.rbac.permission_catalog import (
    PHASE_041_PERMISSIONS,
    PHASE_042_PERMISSIONS,
    PHASE_043_PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)


def _phase_codes() -> set[str]:
    return {
        str(permission["code"])
        for permission in (
            *PHASE_041_PERMISSIONS,
            *PHASE_042_PERMISSIONS,
            *PHASE_043_PERMISSIONS,
        )
    }


def test_phase041_043_permissions_are_unique_and_assigned_to_admin() -> None:
    phase_codes = _phase_codes()
    expected_count = (
        len(PHASE_041_PERMISSIONS)
        + len(PHASE_042_PERMISSIONS)
        + len(PHASE_043_PERMISSIONS)
    )

    assert len(phase_codes) == expected_count
    assert phase_codes.issubset(set(ROLE_PERMISSION_MATRIX["LOGISTICS_ADMIN"]))


def test_phase041_043_required_read_permissions_are_present() -> None:
    phase_codes = _phase_codes()

    assert "logistics.quality_plan.read" in phase_codes
    assert "logistics.quality_quarantine.read" in phase_codes
    assert "logistics.putaway.read" in phase_codes


def test_phase041_043_rbac_sync_follows_phase044_sync() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "gj440410044rb_sync_phase041_043_rbac_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("phase041_043_rbac_sync", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "gj440410044rb"
    assert migration.down_revision == "gi440310044rb"
    assert migration._stable_id(
        "permission", "logistics.putaway.read"
    ) == migration._stable_id("permission", "logistics.putaway.read")
