"""Permission service — effective permission resolution, authorization, seed."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.permission_catalog import (
    CATALOG_VERSION,
    PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)
from app.modules.logistics.rbac.permission_repository import (
    PermissionRepository,
    RolePermissionRepository,
)
from app.modules.logistics.rbac.permission_schemas import (
    AuthorizationCheckResponse,
    EffectivePermissionsResponse,
)
from app.modules.logistics.rbac.repository import (
    RoleAssignmentRepository,
    RoleRepository,
)


class PermissionService:
    def __init__(self) -> None:
        self.perm_repo = PermissionRepository()
        self.role_perm_repo = RolePermissionRepository()
        self.role_repo = RoleRepository()
        self.assignment_repo = RoleAssignmentRepository()

    def list_permissions(self, db: Session, category: str | None = None, status: str | None = None) -> list:
        return self.perm_repo.list(db, category=category, status=status)

    def get_permission(self, db: Session, perm_id: UUID) -> object:
        perm = self.perm_repo.get_by_id(db, perm_id)
        if not perm:
            raise ApplicationError("PERMISSION_NOT_FOUND", "El permiso no existe.", 404)
        return perm

    def get_role_permissions(self, db: Session, role_id: UUID) -> list:
        role = self.role_repo.get_by_id(db, role_id)
        if not role:
            raise ApplicationError("LOGISTICS_ROLE_NOT_FOUND", "El rol no existe.", 404)
        return self.role_perm_repo.list_by_role(db, role_id)

    def resolve_effective_permissions(
        self,
        db: Session,
        user_id: UUID,
        *,
        assignments: Sequence[LogisticsRoleAssignment] | None = None,
    ) -> EffectivePermissionsResponse:
        # 1. Get active role assignments
        active_assignments = (
            list(assignments)
            if assignments is not None
            else self.assignment_repo.list_active_by_user(db, user_id)
        )
        if not active_assignments:
            return EffectivePermissionsResponse(
                catalog_version=CATALOG_VERSION,
                user_id=user_id,
                permissions=[],
                sensitive_permissions=[],
                step_up_permissions=[],
                roles=[],
            )

        # 2. Get role IDs
        role_ids = list(dict.fromkeys(a.role_id for a in active_assignments))

        # 3. Get permission codes for those roles
        perm_codes = self.role_perm_repo.list_permission_codes_by_roles(db, role_ids)

        # 4. Load permission metadata in one query instead of one query per code.
        permissions_by_code = {
            permission.code: permission
            for permission in self.perm_repo.list_by_codes(db, perm_codes)
        }
        sensitive = [
            code
            for code in perm_codes
            if permissions_by_code.get(code)
            and permissions_by_code[code].is_sensitive
        ]
        step_up = [
            code
            for code in perm_codes
            if permissions_by_code.get(code)
            and permissions_by_code[code].requires_step_up
        ]

        # 5. Load role metadata in one query and build the assignment summary.
        roles_by_id = {
            role.id: role for role in self.role_repo.list_by_ids(db, role_ids)
        }
        roles_summary = []
        for assignment in active_assignments:
            role = roles_by_id.get(assignment.role_id)
            if role:
                roles_summary.append({
                    "role_code": role.code,
                    "role_name": role.name,
                    "scope_type": assignment.scope_type.upper(),
                    "organization_id": str(assignment.organization_id)
                    if assignment.organization_id
                    else None,
                    "branch_id": str(assignment.branch_id)
                    if assignment.branch_id
                    else None,
                    "warehouse_id": str(assignment.warehouse_id)
                    if assignment.warehouse_id
                    else None,
                    "expires_at": assignment.ends_at.isoformat()
                    if assignment.ends_at
                    else None,
                })

        return EffectivePermissionsResponse(
            catalog_version=CATALOG_VERSION,
            user_id=user_id,
            permissions=sorted(perm_codes),
            sensitive_permissions=sorted(sensitive),
            step_up_permissions=sorted(step_up),
            roles=roles_summary,
        )

    def check_permission(self, db: Session, user_id: UUID, permission_code: str,
                         organization_id: UUID | None = None, branch_id: UUID | None = None,
                         warehouse_id: UUID | None = None) -> AuthorizationCheckResponse:
        effective = self.resolve_effective_permissions(db, user_id)
        if permission_code not in effective.permissions:
            return AuthorizationCheckResponse(
                allowed=False, permission_code=permission_code,
                reason="PERMISSION_DENIED",
            )
        # Scope validation is handled by the dependency layer
        return AuthorizationCheckResponse(allowed=True, permission_code=permission_code)


# ---------------------------------------------------------------------------
# Seed service — idempotent registration of permissions and role-permission matrix
# ---------------------------------------------------------------------------

class PermissionSeedService:
    def __init__(self) -> None:
        self.perm_repo = PermissionRepository()
        self.role_perm_repo = RolePermissionRepository()
        self.role_repo = RoleRepository()

    def seed_permissions(self, db: Session) -> dict[str, int]:
        created = 0
        reused = 0
        for perm_def in PERMISSIONS:
            existing = self.perm_repo.get_by_code(db, perm_def["code"])
            if existing:
                # Update name/description, preserve code
                if existing.name != perm_def["name"]:
                    existing.name = perm_def["name"]
                if existing.description != perm_def["description"]:
                    existing.description = perm_def["description"]
                if existing.risk_level != perm_def["risk_level"]:
                    existing.risk_level = perm_def["risk_level"]
                if existing.is_sensitive != perm_def.get("is_sensitive", False):
                    existing.is_sensitive = perm_def.get("is_sensitive", False)
                if existing.requires_reason != perm_def.get("requires_reason", False):
                    existing.requires_reason = perm_def.get("requires_reason", False)
                if existing.requires_step_up != perm_def.get("requires_step_up", False):
                    existing.requires_step_up = perm_def.get("requires_step_up", False)
                reused += 1
            else:
                self.perm_repo.create(
                    db,
                    code=perm_def["code"],
                    resource=perm_def["resource"],
                    action=perm_def["action"],
                    name=perm_def["name"],
                    description=perm_def["description"],
                    category=perm_def["category"],
                    risk_level=perm_def["risk_level"],
                    is_sensitive=perm_def.get("is_sensitive", False),
                    requires_reason=perm_def.get("requires_reason", False),
                    requires_step_up=perm_def.get("requires_step_up", False),
                    is_system=True,
                    status="active",
                )
                created += 1
        db.commit()
        return {"created": created, "reused": reused}

    def seed_role_permission_matrix(self, db: Session) -> dict[str, int]:
        granted = 0
        skipped = 0
        for role_code, perm_codes in ROLE_PERMISSION_MATRIX.items():
            role = self.role_repo.get_by_code(db, role_code)
            if not role:
                skipped += len(perm_codes)
                continue
            existing_codes = set(self.role_perm_repo.list_permission_codes_by_role(db, role.id))
            for code in perm_codes:
                if code in existing_codes:
                    continue
                perm = self.perm_repo.get_by_code(db, code)
                if not perm:
                    skipped += 1
                    continue
                self.role_perm_repo.grant(db, role.id, perm.id)
                granted += 1
        db.commit()
        return {"granted": granted, "skipped": skipped}
