from collections.abc import Callable

from fastapi import Depends

from app.core.exceptions import ApplicationError
from app.models.user import User
from app.dependencies.auth import require_active_user


def require_permissions(*roles: str) -> Callable[..., User]:
    def dependency(user: User = Depends(require_active_user)) -> User:
        if user.role not in roles:
            raise ApplicationError(
                "PERMISSION_DENIED", "No tiene permiso para esta operación.", 403
            )
        return user

    return dependency
