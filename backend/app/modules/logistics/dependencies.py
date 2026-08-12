"""Logistics module — adapter dependencies for authentication.

Reuses the existing authentication system without duplicating any
session, CSRF, or user logic.  Provides convenience wrappers that
logistics sub-modules can import without reaching into ``app.dependencies``
directly.
"""

from collections.abc import Callable

from fastapi import Depends

from app.dependencies.auth import get_current_session, get_current_user, require_active_user
from app.dependencies.csrf import verify_csrf
from app.models.session import UserSession
from app.models.user import User
from app.modules.logistics.exceptions import LogisticsPermissionError
from app.modules.logistics.constants import LogisticsPermission


def get_logistics_current_session(
    user_session: UserSession = Depends(get_current_session),
) -> UserSession:
    """Reuse the existing session dependency for logistics routes."""
    return user_session


def get_logistics_current_user(
    user: User = Depends(get_current_user),
) -> User:
    """Reuse the existing user dependency for logistics routes."""
    return user


def require_logistics_permission(
    *permissions: LogisticsPermission,
) -> Callable[..., User]:
    """Return a dependency that checks the user has at least one logistics permission.

    In this phase permissions are not yet assigned to roles — the check
    always passes for active users.  The hook is here so Phase 005 can
    wire the real RBAC matrix without touching every route.
    """

    def dependency(user: User = Depends(require_active_user)) -> User:
        # Phase 003: permission enforcement is deferred.
        # When RBAC is wired (Phase 005), replace this with a real check
        # against user.role → permissions mapping.
        return user

    return dependency


__all__ = [
    "get_logistics_current_session",
    "get_logistics_current_user",
    "require_logistics_permission",
    "verify_csrf",
]