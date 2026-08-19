"""Logistics access context resolver — builds LogisticsPrincipal from session."""

from sqlalchemy.orm import Session

from app.models.session import UserSession
from app.models.user import User
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.rbac.permission_service import PermissionService
from app.modules.logistics.rbac.repository import RoleAssignmentRepository

_permission_service = PermissionService()
_assignment_repo = RoleAssignmentRepository()


class LogisticsAccessResolver:
    """Resolves the full logistics context for an authenticated user."""

    def resolve(self, db: Session, user: User, session: UserSession,
                correlation_id: str | None = None,
                ip_address: str | None = None,
                user_agent: str | None = None) -> LogisticsPrincipal:
        # 1. Resolve assignments once and reuse them for permissions and scope.
        assignments = _assignment_repo.list_active_by_user(db, user.id)
        effective = _permission_service.resolve_effective_permissions(
            db,
            user.id,
            assignments=assignments,
        )

        # 2. Extract organization/branch/warehouse IDs from assignments
        org_ids = list({str(a.organization_id) for a in assignments if a.organization_id})
        branch_ids = list({str(a.branch_id) for a in assignments if a.branch_id})
        wh_ids = list({str(a.warehouse_id) for a in assignments if a.warehouse_id})

        # 3. Determine default context
        default_org = org_ids[0] if len(org_ids) == 1 else None
        default_branch = branch_ids[0] if len(branch_ids) == 1 else None
        default_wh = wh_ids[0] if len(wh_ids) == 1 else None

        # 4. Determine if logistics is enabled
        # Ya no se habilita por rol de plataforma: el acceso al dominio logístico se
        # deriva de tener permisos efectivos, que es lo que concede el catálogo.
        logistics_enabled = len(effective.permissions) > 0

        return LogisticsPrincipal(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            platform_role=user.role,
            is_active=user.is_active,
            session_id=session.id,
            device_id=session.device_id,
            authentication_level=session.authentication_level,
            session_expires_at=session.expires_at,
            risk_score=float(session.risk_score) if session.risk_score else None,
            logistics_enabled=logistics_enabled,
            role_codes=[r["role_code"] for r in effective.roles],
            permission_codes=effective.permissions,
            sensitive_permissions=effective.sensitive_permissions,
            step_up_permissions=effective.step_up_permissions,
            organization_ids=org_ids,
            branch_ids=branch_ids,
            warehouse_ids=wh_ids,
            default_organization_id=default_org,
            default_branch_id=default_branch,
            default_warehouse_id=default_wh,
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )


access_resolver = LogisticsAccessResolver()
