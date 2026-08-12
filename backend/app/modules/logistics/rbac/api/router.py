"""RBAC API router — role catalog, assignments, effective roles, conflicts."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_active_user
from app.dependencies.csrf import verify_csrf
from app.models.user import User
from app.modules.logistics.rbac.permission_schemas import (
    AuthorizationCheckRequest,
    AuthorizationCheckResponse,
    EffectivePermissionsResponse,
    PermissionResponse,
    RolePermissionResponse,
)
from app.modules.logistics.rbac.schemas import (
    EffectiveRolesResponse,
    RoleAssignmentCreate,
    RoleAssignmentDateUpdate,
    RoleAssignmentResponse,
    RoleAssignmentRevoke,
    RoleConflictValidationResponse,
    RoleResponse,
    RoleScopeRuleResponse,
)
from app.modules.logistics.rbac.permission_service import PermissionService
from app.modules.logistics.rbac.service import (
    RoleAssignmentService,
    RoleService,
)
from app.schemas.common import PaginatedResponse


def _create_rbac_router() -> APIRouter:
    router = APIRouter()
    role_service = RoleService()
    assignment_service = RoleAssignmentService()

    # ------------------------------------------------------------------
    # Role catalog
    # ------------------------------------------------------------------
    @router.get("/roles", response_model=list[RoleResponse])
    def list_roles(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        status: str | None = Query(None),
    ):
        return [RoleResponse.model_validate(r) for r in role_service.list(db, status=status)]

    @router.get("/roles/{role_id}", response_model=RoleResponse)
    def get_role(
        role_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return RoleResponse.model_validate(role_service.get(db, role_id))

    @router.get("/roles/{role_id}/scope-rules", response_model=list[RoleScopeRuleResponse])
    def get_role_scope_rules(
        role_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        rules = role_service.get_scope_rules(db, role_id)
        return [RoleScopeRuleResponse.model_validate(r) for r in rules]

    # ------------------------------------------------------------------
    # Effective roles for current user
    # ------------------------------------------------------------------
    @router.get("/me/roles", response_model=EffectiveRolesResponse)
    def get_my_effective_roles(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return assignment_service.resolve_effective_roles(db, user.id)

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------
    @router.post("/role-assignments", response_model=RoleAssignmentResponse, status_code=201)
    def create_assignment(
        data: RoleAssignmentCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        # Only admins can assign roles (temporary until Phase 006)
        if user.role != "admin":
            from app.core.exceptions import ApplicationError
            raise ApplicationError("INSUFFICIENT_ASSIGNMENT_AUTHORITY", "No tiene autoridad para asignar roles.", 403)
        assignment = assignment_service.assign(db, data, user)
        db.commit()
        return RoleAssignmentResponse.model_validate(assignment)

    @router.get("/role-assignments/{assignment_id}", response_model=RoleAssignmentResponse)
    def get_assignment(
        assignment_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return RoleAssignmentResponse.model_validate(assignment_service.get(db, assignment_id))

    @router.get("/users/{user_id}/role-assignments", response_model=PaginatedResponse[RoleAssignmentResponse])
    def list_user_assignments(
        user_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: str | None = Query(None),
    ):
        return assignment_service.list_by_user(db, user_id, status=status, page=page, page_size=page_size)

    @router.patch("/role-assignments/{assignment_id}/dates", response_model=RoleAssignmentResponse)
    def update_assignment_dates(
        assignment_id: UUID,
        data: RoleAssignmentDateUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        assignment = assignment_service.update_dates(db, assignment_id, data.starts_at, data.ends_at, user)
        db.commit()
        return RoleAssignmentResponse.model_validate(assignment)

    @router.post("/role-assignments/{assignment_id}/revoke", response_model=RoleAssignmentResponse)
    def revoke_assignment(
        assignment_id: UUID,
        data: RoleAssignmentRevoke,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        if user.role != "admin":
            from app.core.exceptions import ApplicationError
            raise ApplicationError("INSUFFICIENT_ASSIGNMENT_AUTHORITY", "No tiene autoridad para revocar roles.", 403)
        assignment = assignment_service.revoke(db, assignment_id, data.revocation_reason, user)
        db.commit()
        return RoleAssignmentResponse.model_validate(assignment)

    # ------------------------------------------------------------------
    # Conflict validation
    # ------------------------------------------------------------------
    @router.post("/role-assignments/validate-conflicts", response_model=RoleConflictValidationResponse)
    def validate_conflicts(
        role_a_id: UUID = Query(...),
        role_b_id: UUID = Query(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        result = assignment_service.validate_conflicts(db, role_a_id, role_b_id)
        return RoleConflictValidationResponse(success=True, **result)

    # ------------------------------------------------------------------
    # Permissions catalog
    # ------------------------------------------------------------------
    perm_service = PermissionService()

    @router.get("/permissions", response_model=list[PermissionResponse])
    def list_permissions(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        category: str | None = Query(None),
        status: str | None = Query(None),
    ):
        return [PermissionResponse.model_validate(p) for p in perm_service.list_permissions(db, category=category, status=status)]

    @router.get("/permissions/{permission_id}", response_model=PermissionResponse)
    def get_permission(
        permission_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return PermissionResponse.model_validate(perm_service.get_permission(db, permission_id))

    @router.get("/roles/{role_id}/permissions", response_model=list[RolePermissionResponse])
    def get_role_permissions(
        role_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return [RolePermissionResponse.model_validate(rp) for rp in perm_service.get_role_permissions(db, role_id)]

    @router.get("/me/permissions", response_model=EffectivePermissionsResponse)
    def get_my_permissions(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return perm_service.resolve_effective_permissions(db, user.id)

    @router.post("/authorization/check", response_model=AuthorizationCheckResponse)
    def check_authorization(
        data: AuthorizationCheckRequest,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return perm_service.check_permission(
            db, user.id, data.permission_code,
            data.organization_id, data.branch_id, data.warehouse_id,
        )

    return router