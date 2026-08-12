"""Regression coverage for workflow RBAC permissions used by rendered pages."""

import importlib.util
from pathlib import Path

from app.modules.logistics.rbac.permission_catalog import (
    LEGACY_WORKFLOW_PERMISSIONS,
    PHASE_038_PERMISSIONS,
    PHASE_040_PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)


def _workflow_codes() -> set[str]:
    return {
        str(permission["code"])
        for permission in (
            *PHASE_038_PERMISSIONS,
            *PHASE_040_PERMISSIONS,
            *LEGACY_WORKFLOW_PERMISSIONS,
        )
    }


def test_rendered_workflow_read_permissions_are_in_admin_role() -> None:
    codes = _workflow_codes()

    assert {
        "logistics.gate_check_ins.read",
        "logistics.warehouse_docks.read",
        "logistics.inbound_dock_queue.read",
        "logistics.reception_difference_cases.read",
        "logistics.purchase_requisitions.read",
        "logistics.purchase_requisitions.review",
        "logistics.procurement_approvals.read",
        "logistics.procurement_approval_policies.read",
    }.issubset(codes)
    assert codes.issubset(set(ROLE_PERMISSION_MATRIX["LOGISTICS_ADMIN"]))


def test_workflow_rbac_sync_follows_cost_center_sync() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "gl440610044rb_sync_workflow_rbac_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("workflow_rbac_sync", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "gl440610044rb"
    assert migration.down_revision == "gk440510044rb"
    assert migration._stable_id(
        "permission", "logistics.gate_check_ins.read"
    ) == migration._stable_id("permission", "logistics.gate_check_ins.read")
