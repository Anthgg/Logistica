from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.i18n import (
    negotiate_locale,
    reset_current_locale,
    set_current_locale,
)


def _append_vary(response: Response, header_name: str) -> None:
    values = [
        value.strip()
        for value in response.headers.get("Vary", "").split(",")
        if value.strip()
    ]
    if header_name.lower() not in {value.lower() for value in values}:
        values.append(header_name)
    response.headers["Vary"] = ", ".join(values)


class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        locale = negotiate_locale(request.headers.get("accept-language"))
        request.state.locale = locale
        token = set_current_locale(locale)
        try:
            response = await call_next(request)
            response.headers["Content-Language"] = locale
            _append_vary(response, "Accept-Language")
            return response
        finally:
            reset_current_locale(token)
