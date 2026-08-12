from fastapi import Header, Request

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.security import secure_compare


def verify_csrf(
    request: Request,
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    if not csrf_cookie or not csrf_header or not secure_compare(csrf_cookie, csrf_header):
        raise ApplicationError(
            "CSRF_VALIDATION_FAILED",
            "La validación CSRF falló. Solicite un token nuevo.",
            403,
        )
