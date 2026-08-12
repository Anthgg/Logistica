"""Logistics authentication dependencies — FastAPI integration layer.

These dependencies bridge the existing auth system with the logistics
domain. No second authentication system is created — they simply wrap
get_current_session and resolve logistics context.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.dependencies.auth import get_current_session, get_current_user, require_active_user
from app.dependencies.csrf import verify_csrf
from app.models.session import UserSession
from app.models.user import User
from app.modules.logistics.access_resolver import access_resolver
from app.modules.logistics.principal import LogisticsPrincipal


def get_logistics_principal(
    request: Request,
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> LogisticsPrincipal:
    """Build a LogisticsPrincipal from the current authenticated session.

    This is the primary dependency for all logistics endpoints.
    It reuses the existing get_current_session dependency — no
    duplicate cookie reading, session validation, or user lookup.
    """
    correlation_id = getattr(request.state, "request_id", None)
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() if request.headers.get("x-forwarded-for") else (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")

    return access_resolver.resolve(
        db, session.user, session,
        correlation_id=correlation_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )


def require_logistics_principal(
    principal: LogisticsPrincipal = Depends(get_logistics_principal),
) -> LogisticsPrincipal:
    """Ensure the user has at least some logistics access.

    Users without any logistics permissions get a controlled response
    rather than a hard 403 — the endpoint can show enabled=false.
    This is for endpoints that should work for all authenticated users
    (like /api/logistics/me).
    """
    return principal


def require_logistics_access(
    principal: LogisticsPrincipal = Depends(get_logistics_principal),
) -> LogisticsPrincipal:
    """Require that the user has logistics access (at least one permission).

    Use this for endpoints that should reject users without any
    logistics permissions.
    """
    if not principal.is_platform_admin and not principal.has_logistics_access:
        raise ApplicationError(
            "LOGISTICS_ACCESS_DISABLED",
            "No tiene acceso al dominio logístico.",
            403,
        )
    return principal


def require_permission(permission_code: str):
    """Require a permission and its step-up proof when the catalog demands one."""
    def dependency(
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        db: Session = Depends(get_db),
        x_step_up_proof_id: str | None = Header(
            default=None,
            alias="X-Step-Up-Proof-ID",
        ),
    ) -> LogisticsPrincipal:
        if not principal.is_platform_admin and not principal.has_permission(permission_code):
            raise ApplicationError(
                "FORBIDDEN",
                f"No tiene el permiso requerido '{permission_code}'.",
                403,
            )

        if (
            not principal.is_platform_admin
            and permission_code in principal.step_up_permissions
        ):
            from app.modules.logistics.security.step_up_service import step_up_service

            if not x_step_up_proof_id:
                raise ApplicationError(
                    "STEP_UP_REQUIRED",
                    "Esta acción requiere verificación reforzada.",
                    403,
                )

            proof = step_up_service.find_valid_proof(
                db,
                principal.user_id,
                principal.session_id,
                permission_code,
            )
            if proof is None or str(proof.id) != x_step_up_proof_id:
                raise ApplicationError(
                    "STEP_UP_PROOF_NOT_FOUND",
                    "La verificación reforzada no es válida o ha expirado.",
                    403,
                )

            step_up_service.consume_proof(db, proof)
            db.commit()

        return principal
    return dependency


DEFAULT_LOGISTICS_ORGANIZATION_ID = UUID("f8545a6d-4183-478b-8be2-0df2867475a2")


def resolve_organization_id(principal: LogisticsPrincipal, x_org_id: Optional[str] = None) -> UUID:
    """Resolve the active organization from the authenticated logistics scope.

    The platform ``User`` model intentionally has no ``organization_id``.
    Organization membership belongs to logistics role assignments and is
    exposed through ``LogisticsPrincipal`` instead.
    """
    if x_org_id:
        try:
            return UUID(str(x_org_id))
        except (TypeError, ValueError):
            pass
    organization_id = principal.default_organization_id
    if organization_id is None and principal.organization_ids:
        organization_id = principal.organization_ids[0]
    if organization_id is None and (principal.platform_role == "admin" or principal.logistics_enabled):
        organization_id = DEFAULT_LOGISTICS_ORGANIZATION_ID
    if organization_id is None:
        raise ApplicationError(
            "LOGISTICS_ORGANIZATION_REQUIRED",
            "No se encontró una organización válida en el contexto de sesión.",
            400,
        )
    try:
        return UUID(str(organization_id))
    except (TypeError, ValueError) as exc:
        raise ApplicationError(
            "LOGISTICS_ORGANIZATION_INVALID",
            "La organización del contexto de sesión no es válida.",
            400,
        ) from exc


__all__ = [
    "get_logistics_principal",
    "require_logistics_principal",
    "require_logistics_access",
    "require_permission",
    "resolve_organization_id",
    "verify_csrf",
]
