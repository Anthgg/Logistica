"""Inspect or repair the Phase 044 RBAC catalog without changing Alembic stamps."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.database.session import engine
from app.modules.logistics.rbac.permission_catalog import PHASE_044_PERMISSIONS

REQUIRED_PERMISSION = "logistics.inventory_ledger.read"
INVENTORY_TABLES = (
    "inventory_ledger_partitions",
    "inventory_movements",
    "inventory_movement_lines",
)


def _load_migration() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "gi440310044rb_sync_phase044_rbac_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("phase044_rbac_sync", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load migration: {path.name}")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _snapshot(connection: sa.Connection) -> dict[str, object]:
    phase_codes = [str(permission["code"]) for permission in PHASE_044_PERMISSIONS]
    permissions = sa.table(
        "logistics_permissions",
        sa.column("id"),
        sa.column("code"),
    )
    roles = sa.table(
        "logistics_roles",
        sa.column("id"),
        sa.column("code"),
    )
    role_permissions = sa.table(
        "logistics_role_permissions",
        sa.column("role_id"),
        sa.column("permission_id"),
        sa.column("effect"),
    )
    alembic_version = sa.table("alembic_version", sa.column("version_num"))

    total_permissions = connection.scalar(
        sa.select(sa.func.count()).select_from(permissions)
    )
    phase_permissions = connection.scalar(
        sa.select(sa.func.count())
        .select_from(permissions)
        .where(permissions.c.code.in_(phase_codes))
    )
    required_exists = connection.scalar(
        sa.select(sa.func.count())
        .select_from(permissions)
        .where(permissions.c.code == REQUIRED_PERMISSION)
    )
    admin_phase_permissions = connection.scalar(
        sa.select(sa.func.count())
        .select_from(
            role_permissions.join(
                roles,
                roles.c.id == role_permissions.c.role_id,
            ).join(
                permissions,
                permissions.c.id == role_permissions.c.permission_id,
            )
        )
        .where(
            roles.c.code == "LOGISTICS_ADMIN",
            permissions.c.code.in_(phase_codes),
            role_permissions.c.effect == "allow",
        )
    )
    revisions = list(connection.scalars(sa.select(alembic_version.c.version_num)))
    inspector = sa.inspect(connection)

    return {
        "alembic_revisions": revisions,
        "inventory_tables": {
            table_name: inspector.has_table(table_name)
            for table_name in INVENTORY_TABLES
        },
        "total_permissions": total_permissions,
        "phase044_permissions": phase_permissions,
        "phase044_expected": len(phase_codes),
        "required_permission_exists": bool(required_exists),
        "logistics_admin_phase044_permissions": admin_phase_permissions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the idempotent Phase 044 catalog repair in one transaction.",
    )
    args = parser.parse_args()

    with engine.begin() as connection:
        before = _snapshot(connection)
        if args.apply:
            migration = _load_migration()
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()
        after = _snapshot(connection)

    print(
        json.dumps(
            {"applied": args.apply, "before": before, "after": after},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
