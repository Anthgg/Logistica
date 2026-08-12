import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.i18n import (
    locale_from_request,
    translate_error,
    translate_validation_message,
)

logger = logging.getLogger("app.errors")


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _error_response(
    request: Request,
    code: str,
    message: str,
    details: Any = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    locale = locale_from_request(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": translate_error(code, message, locale),
                "details": details,
            },
        },
        headers={
            "Content-Language": locale,
            "Vary": "Accept-Language",
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    locale = locale_from_request(request)
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": translate_validation_message(error["type"], locale),
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _error_response(
        request,
        "VALIDATION_ERROR",
        "Los datos enviados no son válidos.",
        details,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    messages = {
        status.HTTP_401_UNAUTHORIZED: ("AUTHENTICATION_ERROR", "Se requiere autenticación."),
        status.HTTP_403_FORBIDDEN: ("PERMISSION_DENIED", "No tiene permiso para esta operación."),
        status.HTTP_404_NOT_FOUND: ("RESOURCE_NOT_FOUND", "El recurso solicitado no existe."),
        status.HTTP_405_METHOD_NOT_ALLOWED: (
            "METHOD_NOT_ALLOWED",
            "El método HTTP no está permitido para este recurso.",
        ),
    }
    code, message = messages.get(
        exc.status_code,
        ("HTTP_ERROR", str(exc.detail) if exc.detail else "La solicitud no pudo procesarse."),
    )
    response = _error_response(request, code, message, status_code=exc.status_code)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unavailable")
    logger.exception("request_id=%s | Unexpected internal error", request_id, exc_info=exc)
    return _error_response(
        request,
        "INTERNAL_SERVER_ERROR",
        "Ocurrió un error interno. Inténtelo nuevamente más tarde.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def application_exception_handler(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    return _error_response(
        request,
        exc.code,
        exc.message,
        status_code=exc.status_code,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, application_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
