"""Security dependencies for the inventory-ledger router.

The decorators remain non-wrapping metadata markers so FastAPI can inspect the
original endpoint signature.  :func:`enforce_inventory_route_security` reads
that metadata at request time and enforces permission, organization scope,
step-up and CSRF through the existing logistics security stack.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import ParamSpec, TypeVar
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.principal import LogisticsPrincipal

P = ParamSpec("P")
R = TypeVar("R")


class StepUpLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def require_capability(capability: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Mark a handler with the required capability.

    Returns the original function unchanged. The capability is exposed
    via ``func.__inventory_capability__`` for downstream auditing and
    permission resolution.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        setattr(func, "__inventory_capability__", capability)
        return func

    return decorator


def require_step_up(level: StepUpLevel) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Mark a handler with the minimum required step-up level."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        setattr(func, "__inventory_step_up_level__", level.value)
        return func

    return decorator


def require_csrf(func: Callable[P, R]) -> Callable[P, R]:
    """Mark a handler as requiring CSRF verification."""

    setattr(func, "__inventory_requires_csrf__", True)
    return func


def enforce_inventory_route_security(
    request: Request,
    principal: LogisticsPrincipal = Depends(get_logistics_principal),
    db: Session = Depends(get_db),
    x_step_up_proof_id: str | None = Header(
        default=None,
        alias="X-Step-Up-Proof-ID",
    ),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> LogisticsPrincipal:
    """Enforce the metadata attached to the currently selected endpoint."""

    endpoint = request.scope.get("endpoint")
    capability = getattr(endpoint, "__inventory_capability__", None)
    step_up_level = getattr(endpoint, "__inventory_step_up_level__", None)
    requires_csrf = bool(getattr(endpoint, "__inventory_requires_csrf__", False))

    if capability and not principal.is_platform_admin and not principal.has_permission(capability):
        raise ApplicationError(
            "FORBIDDEN",
            f"No tiene el permiso requerido '{capability}'.",
            403,
        )

    organization_value = request.path_params.get("organization_id")
    if organization_value is None:
        organization_value = request.query_params.get("organization_id")
    if organization_value is not None and not principal.is_platform_admin:
        try:
            organization_id = UUID(str(organization_value))
        except (TypeError, ValueError) as exc:
            raise ApplicationError(
                "LOGISTICS_ORGANIZATION_INVALID",
                "La organización solicitada no es válida.",
                400,
            ) from exc
        if not principal.can_access_organization(organization_id):
            raise ApplicationError(
                "FORBIDDEN_ORGANIZATION_SCOPE",
                "No tiene acceso a la organización solicitada.",
                403,
            )

    if (
        capability
        and step_up_level not in {None, StepUpLevel.LOW.value}
        and not principal.is_platform_admin
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
            capability,
        )
        if proof is None or str(proof.id) != x_step_up_proof_id:
            raise ApplicationError(
                "STEP_UP_PROOF_NOT_FOUND",
                "La verificación reforzada no es válida o ha expirado.",
                403,
            )
        step_up_service.consume_proof(db, proof)
        db.commit()

    if requires_csrf:
        verify_csrf(request, x_csrf_token)

    return principal
