"""FastAPI dependency for logistics permission enforcement with step-up.

Usage:
    @router.post("/warehouses", dependencies=[Depends(
        require_logistics_permission("logistics.warehouses.create")
    )])

For sensitive permissions (those in POLICY_CATALOG), the caller must
provide a valid StepUpProof. The proof is consumed if one-time.
"""

from collections.abc import Callable

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.dependencies.auth import require_active_user
from app.models.user import User
from app.modules.logistics.rbac.permission_service import PermissionService
from app.modules.logistics.security.step_up_policy import is_sensitive_permission
from app.modules.logistics.security.step_up_service import step_up_service


_service = PermissionService()


def require_logistics_permission(
    permission_code: str,
) -> Callable[..., User]:
    """Return a FastAPI dependency that checks the user has the given permission.

    For sensitive permissions, also validates a step-up proof.
    Platform admin bypasses temporarily until full RBAC migration.
    """

    def dependency(
        request: Request,
        user: User = Depends(require_active_user),
        db: Session = Depends(get_db),
        x_step_up_proof_id: str | None = Header(default=None, alias="X-Step-Up-Proof-ID"),
    ) -> User:
        # Temporary: platform admin bypasses until full migration
        if user.role == "admin":
            return user

        # Resolve effective permissions
        effective = _service.resolve_effective_permissions(db, user.id)

        if permission_code not in effective.permissions:
            # Audit the denial
            _audit_denial(db, request, user, permission_code)
            raise ApplicationError(
                "PERMISSION_DENIED",
                "No tiene permiso para esta operación.",
                403,
            )

        # Check if this permission requires step-up
        if is_sensitive_permission(permission_code):
            # Find the user's session
            from app.dependencies.auth import get_current_session
            session_token = request.cookies.get("session_token")
            if not session_token:
                _audit_denial(db, request, user, permission_code, "NO_SESSION")
                raise ApplicationError(
                    "STEP_UP_REQUIRED",
                    "Esta acción requiere verificación adicional.",
                    403,
                )

            from app.services.session_service import SessionService
            session = SessionService().authenticate(db, session_token)

            # Look for a valid proof
            if not x_step_up_proof_id:
                _audit_denial(db, request, user, permission_code, "NO_PROOF")
                raise ApplicationError(
                    "STEP_UP_REQUIRED",
                    "Esta acción requiere verificación reforzada.",
                    403,
                )

            proof = step_up_service.find_valid_proof(
                db, user.id, session.id, permission_code,
            )

            if not proof or str(proof.id) != x_step_up_proof_id:
                _audit_denial(db, request, user, permission_code, "PROOF_INVALID")
                raise ApplicationError(
                    "STEP_UP_PROOF_NOT_FOUND",
                    "La verificación reforzada no es válida o ha expirado.",
                    403,
                )

            # Consume the proof if one-time
            step_up_service.consume_proof(db, proof)
            db.commit()

        return user

    return dependency


def _audit_denial(
    db: Session,
    request: Request,
    user: User,
    permission_code: str,
    reason: str = "PERMISSION_DENIED",
) -> None:
    """Write an audit event for a denied permission check (best-effort)."""
    try:
        from app.modules.logistics.audit.service import AuditService, AuditEventCommand

        client_ip = None
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host

        correlation_id = getattr(request.state, "request_id", None)

        command = AuditEventCommand(
            event_code="logistics.permission.authorization_denied",
            actor_user_id=user.id,
            actor_type="user",
            actor_display_name=user.full_name,
            action="access",
            result="denied",
            reason_code=reason,
            reason_text=f"Permission required: {permission_code}",
            severity="medium",
            endpoint=str(request.url.path) if request.url else None,
            method=request.method,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            correlation_id=correlation_id,
            resource_type="permission",
            resource_id=permission_code,
            source_module="rbac",
            source_service="require_logistics_permission",
            metadata={"permission_code": permission_code, "reason": reason},
        )

        AuditService().write_event(db, command)
        db.commit()
    except Exception:
        db.rollback()