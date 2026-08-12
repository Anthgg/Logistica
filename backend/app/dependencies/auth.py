from collections.abc import Callable

from fastapi import Cookie, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.models.session import UserSession
from app.models.user import User
from app.services.session_service import SessionService

session_service = SessionService()


def get_current_session(
    request: Request,
    database: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
) -> UserSession:
    user_session = session_service.authenticate(database, session_token)
    request.state.current_session = user_session
    request.state.current_user = user_session.user
    return user_session


def get_current_user(
    user_session: UserSession = Depends(get_current_session),
) -> User:
    return user_session.user


def require_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise ApplicationError("ACCOUNT_DISABLED", "La cuenta está desactivada.", 403)
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def role_dependency(user: User = Depends(require_active_user)) -> User:
        if user.role not in allowed_roles:
            raise ApplicationError(
                "PERMISSION_DENIED", "No tiene permiso para esta operación.", 403
            )
        return user

    return role_dependency
