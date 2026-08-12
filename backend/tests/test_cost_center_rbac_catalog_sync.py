"""Regression coverage for the missing cost-center RBAC synchronization."""

import importlib.util
from pathlib import Path

from app.modules.logistics.rbac.permission_catalog import (
    COST_CENTER_PERMISSIONS,
    PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)


def test_cost_center_permissions_are_in_the_catalog_and_admin_role() -> None:
    codes = {str(permission["code"]) for permission in COST_CENTER_PERMISSIONS}
    catalog_codes = {str(permission["code"]) for permission in PERMISSIONS}

    assert codes == {
        "logistics.cost_centers.read",
        "logistics.cost_centers.manage",
    }
    assert codes.issubset(catalog_codes)
    assert codes.issubset(set(ROLE_PERMISSION_MATRIX["LOGISTICS_ADMIN"]))
    assert codes.issubset(set(ROLE_PERMISSION_MATRIX["LOGISTICS_MANAGER"]))


def test_cost_center_read_is_available_to_purchasing_and_audit_roles() -> None:
    for role_code in (
        "PURCHASING",
        "PURCHASING_APPROVER",
        "LOGISTICS_AUDITOR",
        "LOGISTICS_VIEWER",
    ):
        assert "logistics.cost_centers.read" in ROLE_PERMISSION_MATRIX[role_code]
        assert "logistics.cost_centers.manage" not in ROLE_PERMISSION_MATRIX[role_code]


def test_cost_center_sync_is_the_current_successor_of_phase041_043_sync() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "gk440510044rb_sync_cost_center_rbac_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("cost_center_rbac_sync", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "gk440510044rb"
    assert migration.down_revision == "gj440410044rb"
    assert migration._stable_id(
        "permission", "logistics.cost_centers.read"
    ) == migration._stable_id("permission", "logistics.cost_centers.read")
