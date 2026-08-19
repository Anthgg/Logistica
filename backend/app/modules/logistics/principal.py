"""LogisticsPrincipal — unified authenticated context for logistics operations.

This is NOT a second authentication system. It wraps the existing
UserSession + User + logistics roles/permissions into a single
immutable value object that route handlers can use without
re-resolving each piece individually.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class LogisticsPrincipal:
    """Immutable principal carrying everything a logistics route needs."""

    user_id: UUID
    email: str
    full_name: str
    platform_role: str
    is_active: bool

    session_id: UUID
    device_id: UUID | None
    authentication_level: str
    session_expires_at: datetime
    risk_score: float | None

    # Logistics context
    logistics_enabled: bool
    role_codes: list[str] = field(default_factory=list)
    permission_codes: list[str] = field(default_factory=list)
    sensitive_permissions: list[str] = field(default_factory=list)
    step_up_permissions: list[str] = field(default_factory=list)

    # Authorized scopes
    organization_ids: list[str] = field(default_factory=list)
    branch_ids: list[str] = field(default_factory=list)
    warehouse_ids: list[str] = field(default_factory=list)

    # Default context
    default_organization_id: str | None = None
    default_branch_id: str | None = None
    default_warehouse_id: str | None = None

    # Request context
    correlation_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def has_logistics_access(self) -> bool:
        return self.logistics_enabled and len(self.permission_codes) > 0

    @property
    def is_platform_admin(self) -> bool:
        """Rol de plataforma del usuario.

        Se conserva para trazas y diagnóstico, pero **ya no concede autorización**.
        Hasta F006 cortocircuitaba permisos, alcance y step-up: un
        ``users.role == "admin"`` entraba a todo sin pasar por el catálogo, y de paso
        ocultaba que el módulo de evaluaciones exigía siete permisos inexistentes.

        La autoridad es ahora el catálogo. Se comprobó antes de retirarlo que los 81
        administradores activos en producción ya tienen ``LOGISTICS_ADMIN`` asignado
        por la vía normal, así que ninguno pierde acceso.
        """
        return self.platform_role == "admin"

    def has_permission(self, code: str) -> bool:
        return code in self.permission_codes

    def has_any_permission(self, *codes: str) -> bool:
        return any(c in self.permission_codes for c in codes)

    def can_access_organization(self, org_id: str | UUID) -> bool:
        org_str = str(org_id)
        if not self.organization_ids:
            return True  # No scope restriction (global)
        return org_str in self.organization_ids

    def can_access_branch(self, branch_id: str | UUID) -> bool:
        b_str = str(branch_id)
        if not self.branch_ids:
            return True
        return b_str in self.branch_ids

    def can_access_warehouse(self, wh_id: str | UUID) -> bool:
        w_str = str(wh_id)
        if not self.warehouse_ids:
            return True
        return w_str in self.warehouse_ids