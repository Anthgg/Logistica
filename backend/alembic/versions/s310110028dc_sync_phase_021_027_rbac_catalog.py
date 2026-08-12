"""Synchronize the RBAC catalog used by phases 021 through 027.

Revision ID: s310110028dc
Revises: r300110027dc
Create Date: 2026-07-28 20:30:00.000000
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "s280110028a"
down_revision: Union[str, None] = "r300110027dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.modules.logistics.rbac.catalog import SYSTEM_ROLES
    from app.modules.logistics.rbac.permission_catalog import (
        PERMISSIONS,
        ROLE_PERMISSION_MATRIX,
    )

    bind = op.get_bind()

    roles = sa.table(
        "logistics_roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("role_type", sa.String()),
        sa.column("is_system", sa.Boolean()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    role_scope_rules = sa.table(
        "logistics_role_scope_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("allowed_scope_type", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
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
    role_permissions = sa.table(
        "logistics_role_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
        sa.column("effect", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    for role_definition in SYSTEM_ROLES:
        statement = postgresql.insert(roles).values(
            id=uuid4(),
            code=role_definition["code"],
            name=role_definition["name"],
            description=role_definition["description"],
            role_type="system",
            is_system=True,
            status="active",
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
        bind.execute(
            statement.on_conflict_do_update(
                index_elements=[roles.c.code],
                set_={
                    "name": statement.excluded.name,
                    "description": statement.excluded.description,
                    "role_type": "system",
                    "is_system": True,
                    "status": "active",
                    "updated_at": sa.func.now(),
                },
            )
        )

    role_ids = dict(bind.execute(sa.select(roles.c.code, roles.c.id)).all())
    for role_definition in SYSTEM_ROLES:
        role_id = role_ids.get(role_definition["code"])
        if role_id is None:
            continue
        for scope in role_definition["allowed_scopes"]:
            scope_value = scope.value if hasattr(scope, "value") else str(scope)
            statement = postgresql.insert(role_scope_rules).values(
                id=uuid4(),
                role_id=role_id,
                allowed_scope_type=scope_value,
                created_at=sa.func.now(),
            )
            bind.execute(
                statement.on_conflict_do_nothing(
                    index_elements=[
                        role_scope_rules.c.role_id,
                        role_scope_rules.c.allowed_scope_type,
                    ]
                )
            )

    for permission_definition in PERMISSIONS:
        statement = postgresql.insert(permissions).values(
            id=uuid4(),
            code=permission_definition["code"],
            resource=permission_definition["resource"],
            action=permission_definition["action"],
            name=permission_definition["name"],
            description=permission_definition["description"],
            category=permission_definition["category"],
            risk_level=str(permission_definition["risk_level"]),
            is_sensitive=permission_definition.get("is_sensitive", False),
            requires_reason=permission_definition.get("requires_reason", False),
            requires_step_up=permission_definition.get("requires_step_up", False),
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
        bind.execute(sa.select(permissions.c.code, permissions.c.id)).all()
    )
    for role_code, permission_codes in ROLE_PERMISSION_MATRIX.items():
        role_id = role_ids.get(role_code)
        if role_id is None:
            continue
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                continue
            statement = postgresql.insert(role_permissions).values(
                id=uuid4(),
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
    from app.modules.logistics.rbac.permission_catalog import (
        PHASE_021_027_PERMISSIONS,
    )

    phase_codes = [permission["code"] for permission in PHASE_021_027_PERMISSIONS]
    op.execute(
        sa.text("DELETE FROM logistics_permissions WHERE code = ANY(:codes)").bindparams(
            sa.bindparam("codes", value=phase_codes, type_=postgresql.ARRAY(sa.String()))
        )
    )
