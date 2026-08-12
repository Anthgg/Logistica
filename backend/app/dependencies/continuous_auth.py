from collections.abc import Callable

from fastapi import Depends

from app.core.exceptions import ApplicationError
from app.dependencies.auth import get_current_session
from app.models.session import UserSession


def require_continuous_auth_level(
    *allowed_levels: str,
) -> Callable[..., UserSession]:
    permitted = set(allowed_levels) or {
        "traditional",
        "continuously_verified",
    }

    def dependency(
        user_session: UserSession = Depends(get_current_session),
    ) -> UserSession:
        if user_session.revoked_at:
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión fue terminada.", 401
            )
        if (
            user_session.continuous_auth_status == "terminated"
            or user_session.authentication_level == "terminated"
        ):
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión fue terminada.", 403
            )
        if (
            user_session.continuous_auth_status == "restricted"
            or user_session.authentication_level == "restricted"
        ):
            raise ApplicationError(
                "SESSION_RESTRICTED",
                "La sesión no puede ejecutar esta operación.",
                403,
            )
        if user_session.authentication_level not in permitted:
            raise ApplicationError(
                "REVERIFICATION_REQUIRED",
                "La operación requiere reverificación.",
                403,
            )
        return user_session

    return dependency
