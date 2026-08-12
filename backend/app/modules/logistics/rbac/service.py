"""RBAC service — role management, assignment logic, effective roles resolution."""

from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.user import User
from app.modules.logistics.rbac.catalog import SYSTEM_ROLES

ROLE_CATALOG_VERSION = "1.0.0"
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_scope_rule import LogisticsRoleScopeRule
from app.modules.logistics.rbac.repository import (
    RoleAssignmentRepository,
    RoleConflictRepository,
    RoleRepository,
)
from app.modules.logistics.rbac.schemas import (
    EffectiveRoleResponse,
    EffectiveRolesResponse,
    RoleAssignmentCreate,
    RoleAssignmentResponse,
)
from app.schemas.common import PaginatedResponse


class RoleService:
    def __init__(self) -> None:
        self.repo = RoleRepository()

    def list(self, db: Session, status: str | None = None) -> list[LogisticsRole]:
        return self.repo.list(db, status=status)

    def get(self, db: Session, role_id: UUID) -> LogisticsRole:
        role = self.repo.get_by_id(db, role_id)
        if not role:
            raise ApplicationError("LOGISTICS_ROLE_NOT_FOUND", "El rol no existe.", 404)
        return role

    def get_scope_rules(self, db: Session, role_id: UUID) -> list[LogisticsRoleScopeRule]:
        self.get(db, role_id)
        return self.repo.list_scope_rules(db, role_id)


class RoleAssignmentService:
    def __init__(self) -> None:
        self.repo = RoleAssignmentRepository()
        self.role_repo = RoleRepository()
        self.conflict_repo = RoleConflictRepository()

    def get(self, db: Session, assignment_id: UUID) -> LogisticsRoleAssignment:
        assignment = self.repo.get_by_id(db, assignment_id)
        if not assignment:
            raise ApplicationError("ROLE_ASSIGNMENT_NOT_FOUND", "La asignación de rol no existe.", 404)
        return assignment

    def list_by_user(
        self, db: Session, user_id: UUID, *, status: str | None = None,
        page: int = 1, page_size: int = 20,
    ) -> PaginatedResponse[RoleAssignmentResponse]:
        items, total = self.repo.list_by_user(db, user_id, status=status, page=page, page_size=page_size)
        return PaginatedResponse(
            items=[RoleAssignmentResponse.model_validate(i) for i in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    def resolve_effective_roles(self, db: Session, user_id: UUID) -> EffectiveRolesResponse:
        active = self.repo.list_active_by_user(db, user_id)
        items = []
        for a in active:
            role = self.role_repo.get_by_id(db, a.role_id)
            code = role.code if role else "unknown"
            items.append(EffectiveRoleResponse(
                role_code=code,
                role_name=role.name if role else "Desconocido",
                scope_type=a.scope_type.upper(),
                organization_id=a.organization_id,
                branch_id=a.branch_id,
                warehouse_id=a.warehouse_id,
                expires_at=a.ends_at,
            ))
        return EffectiveRolesResponse(
            user_id=user_id,
            roles=items,
        )

    def validate_conflicts(self, db: Session, role_a_id: UUID, role_b_id: UUID) -> dict:
        conflict = self.conflict_repo.get_conflict(db, role_a_id, role_b_id)
        if conflict:
            return {
                "has_conflict": True,
                "conflict_type": conflict.conflict_type,
                "description": conflict.description,
            }
        return {"has_conflict": False, "conflict_type": None, "description": None}

    def assign(self, db: Session, data: RoleAssignmentCreate, actor: User) -> LogisticsRoleAssignment:
        role = self.role_repo.get_by_id(db, data.role_id)
        if not role:
            raise ApplicationError("LOGISTICS_ROLE_NOT_FOUND", "El rol no existe.", 404)
        if role.status != "active":
            raise ApplicationError("ROLE_INACTIVE", "No se puede asignar un rol inactivo.", 409)

        # Check scope rules
        scope_rules = self.role_repo.list_scope_rules(db, data.role_id)
        allowed_scopes = {r.allowed_scope_type for r in scope_rules}
        if allowed_scopes and data.scope_type not in allowed_scopes:
            raise ApplicationError(
                "INVALID_ASSIGNMENT_SCOPE",
                f"El ámbito {data.scope_type} no está permitido para el rol {role.code}.",
                400,
            )

        # Check existing active roles for conflict
        active = self.repo.list_active_by_user(db, data.user_id)
        for a in active:
            check = self.validate_conflicts(db, data.role_id, a.role_id)
            if check["has_conflict"]:
                raise ApplicationError(
                    "ROLE_ASSIGNMENT_CONFLICT",
                    f"Conflicto SoD detectado: {check['description']}",
                    409,
                )

        # Check duplicate active equivalent assignment
        eq = self.repo.find_equivalent(
            db, data.user_id, data.role_id, data.scope_type,
            data.organization_id, data.branch_id, data.warehouse_id,
        )
        if eq:
            raise ApplicationError("DUPLICATE_ROLE_ASSIGNMENT", "La asignación de rol ya existe.", 409)

        assignment = self.repo.create(
            db,
            user_id=data.user_id,
            role_id=data.role_id,
            scope_type=data.scope_type,
            organization_id=data.organization_id,
            branch_id=data.branch_id,
            warehouse_id=data.warehouse_id,
            status="active",
            assigned_by=actor.id,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
        return assignment

    def update_dates(self, db: Session, assignment_id: UUID, starts_at, ends_at, actor: User) -> LogisticsRoleAssignment:
        assignment = self.get(db, assignment_id)
        if assignment.status != "active":
            raise ApplicationError("ROLE_ASSIGNMENT_INACTIVE", "Solo se pueden modificar fechas de asignaciones activas.", 409)
        return self.repo.update_dates(db, assignment, starts_at, ends_at)

    def revoke(self, db: Session, assignment_id: UUID, reason: str, actor: User) -> LogisticsRoleAssignment:
        assignment = self.get(db, assignment_id)
        if assignment.status != "active":
            raise ApplicationError("ROLE_ASSIGNMENT_ALREADY_REVOKED", "La asignación ya ha sido revocada o expirada.", 409)
        return self.repo.revoke(db, assignment, revoked_by=actor.id, reason=reason)


# ---------------------------------------------------------------------------
# Seed service — idempotent registration of system roles
# ---------------------------------------------------------------------------

class RoleSeedService:
    def __init__(self) -> None:
        self.repo = RoleRepository()

    def seed_system_roles(self, db: Session) -> dict[str, int]:
        created = 0
        reused = 0
        for role_def in SYSTEM_ROLES:
            existing = self.repo.get_by_code(db, role_def["code"])
            if existing:
                if existing.name != role_def["name"]:
                    existing.name = role_def["name"]
                if existing.description != role_def["description"]:
                    existing.description = role_def["description"]
                reused += 1
            else:
                role = self.repo.create(
                    db,
                    code=role_def["code"],
                    name=role_def["name"],
                    description=role_def["description"],
                    role_type="system",
                    is_system=True,
                    status="active",
                )
                for scope in role_def["allowed_scopes"]:
                    self.repo.add_scope_rule(db, role.id, scope.value if hasattr(scope, "value") else str(scope))
                created += 1
        db.commit()
        return {"created": created, "reused": reused}