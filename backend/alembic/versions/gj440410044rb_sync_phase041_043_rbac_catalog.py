"""Synchronize the Phase 041-043 logistics RBAC catalog.

Revision ID: gj440410044rb
Revises: gi440310044rb
Create Date: 2026-08-11 01:15:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID, uuid5

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "gj440410044rb"
down_revision: str | Sequence[str] | None = "gi440310044rb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MIGRATION_NAMESPACE = UUID("58e18418-c70e-4bfc-b050-28803660bacb")


def _stable_id(kind: str, value: str) -> UUID:
    return uuid5(_MIGRATION_NAMESPACE, f"{kind}:{value}")


def _phase_permissions() -> list[dict[str, object]]:
    from app.modules.logistics.rbac.permission_catalog import (
        PHASE_041_PERMISSIONS,
        PHASE_042_PERMISSIONS,
        PHASE_043_PERMISSIONS,
    )

    return [
        *PHASE_041_PERMISSIONS,
        *PHASE_042_PERMISSIONS,
        *PHASE_043_PERMISSIONS,
    ]


def upgrade() -> None:
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX

    bind = op.get_bind()
    permissions = sa.table(
        "logistics_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("category", sa.String()),
        sa.column("risk_level", sa.String()),
        sa.column("is_sensitive", sa.Boolean()),
        sa.column("requires_reason", sa.Boolean()),
        sa.column("requires_step_up", sa.Boolean()),
        sa.column("is_system", sa.Boolean()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    roles = sa.table(
        "logistics_roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
    )
    role_permissions = sa.table(
        "logistics_role_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
        sa.column("effect", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    phase_permissions = _phase_permissions()
    phase_codes = [str(permission["code"]) for permission in phase_permissions]

    for permission in phase_permissions:
        code = str(permission["code"])
        statement = postgresql.insert(permissions).values(
            id=_stable_id("permission", code),
            code=code,
            resource=permission["resource"],
            action=permission["action"],
            name=permission["name"],
            description=permission["description"],
            category=permission["category"],
            risk_level=str(permission["risk_level"]),
            is_sensitive=permission.get("is_sensitive", False),
            requires_reason=permission.get("requires_reason", False),
            requires_step_up=permission.get("requires_step_up", False),
            is_system=True,
            status="active",
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
        bind.execute(
            statement.on_conflict_do_update(
                index_elements=[permissions.c.code],
                set_={
                    "resource": statement.excluded.resource,
                    "action": statement.excluded.action,
                    "name": statement.excluded.name,
                    "description": statement.excluded.description,
                    "category": statement.excluded.category,
                    "risk_level": statement.excluded.risk_level,
                    "is_sensitive": statement.excluded.is_sensitive,
                    "requires_reason": statement.excluded.requires_reason,
                    "requires_step_up": statement.excluded.requires_step_up,
                    "is_system": True,
                    "status": "active",
                    "updated_at": sa.func.now(),
                },
            )
        )

    permission_ids = dict(
        bind.execute(
            sa.select(permissions.c.code, permissions.c.id).where(
                permissions.c.code.in_(phase_codes)
            )
        ).all()
    )
    role_ids = dict(bind.execute(sa.select(roles.c.code, roles.c.id)).all())

    for role_code, configured_codes in ROLE_PERMISSION_MATRIX.items():
        role_id = role_ids.get(role_code)
        if role_id is None:
            continue
        for permission_code in configured_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                continue
            statement = postgresql.insert(role_permissions).values(
                id=_stable_id("role-permission", f"{role_code}:{permission_code}"),
                role_id=role_id,
                permission_id=permission_id,
                effect="allow",
                created_at=sa.func.now(),
            )
            bind.execute(
                statement.on_conflict_do_nothing(
                    index_elements=[
                        role_permissions.c.role_id,
                        role_permissions.c.permission_id,
                    ]
                )
            )


def downgrade() -> None:
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX

    bind = op.get_bind()
    role_permissions = sa.table(
        "logistics_role_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    permissions = sa.table(
        "logistics_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )

    phase_permissions = _phase_permissions()
    phase_codes = {str(permission["code"]) for permission in phase_permissions}
    mapping_ids = [
        _stable_id("role-permission", f"{role_code}:{permission_code}")
        for role_code, configured_codes in ROLE_PERMISSION_MATRIX.items()
        for permission_code in configured_codes
        if permission_code in phase_codes
    ]
    permission_ids = [
        _stable_id("permission", str(permission["code"]))
        for permission in phase_permissions
    ]

    bind.execute(sa.delete(role_permissions).where(role_permissions.c.id.in_(mapping_ids)))
    bind.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
