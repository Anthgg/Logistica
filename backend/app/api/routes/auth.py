from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.rate_limit import enforce_auth_rate_limit
from app.core.security import generate_csrf_token
from app.database.base import ensure_utc, utc_now
from app.database.session import get_db
from app.dependencies.auth import get_current_session
from app.dependencies.csrf import verify_csrf
from app.i18n import translate
from app.models.session import UserSession
from app.repositories.session_repository import SessionRepository
from app.schemas.auth import (
    AuthenticatedUser,
    AuthResponse,
    ChangePasswordRequest,
    CsrfResponse,
    CurrentSession,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    SessionSummary,
    SessionsResponse,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
session_repository = SessionRepository()
audit_service = AuditService()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def _set_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: int,
    *,
    httponly: bool,
    samesite: str | None = None,
) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        expires=utc_now() + timedelta(seconds=max_age),
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=httponly,
        samesite=samesite or settings.SESSION_COOKIE_SAMESITE,
    )


def _delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )


@router.get("/csrf", response_model=CsrfResponse)
def csrf(response: Response) -> CsrfResponse:
    token = generate_csrf_token()
    _set_cookie(
        response,
        settings.CSRF_COOKIE_NAME,
        token,
        max_age=3600,
        httponly=False,
    )
    return CsrfResponse(csrf_token=token)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf), Depends(enforce_auth_rate_limit)],
)
def register(
    data: RegisterRequest,
    request: Request,
    database: Session = Depends(get_db),
) -> AuthResponse:
    user = auth_service.register(
        database,
        data,
        _client_ip(request),
        request.headers.get("user-agent"),
    )
    return AuthResponse(
        message=translate("message.auth.registered"),
        user=AuthenticatedUser.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(verify_csrf), Depends(enforce_auth_rate_limit)],
)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
) -> AuthResponse:
    user, user_session, raw_token, raw_refresh_token, device_result = auth_service.login(
        database,
        data,
        request.cookies.get(settings.DEVICE_COOKIE_NAME),
        _client_ip(request),
        request.headers.get("user-agent"),
    )
    refresh_max_age = (
        settings.REMEMBER_SESSION_EXPIRE_DAYS * 86400
        if data.remember_me
        else settings.SESSION_EXPIRE_MINUTES * 60
    )
    _set_cookie(
        response,
        settings.SESSION_COOKIE_NAME,
        raw_token,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    _set_cookie(
        response,
        settings.REFRESH_COOKIE_NAME,
        raw_refresh_token,
        refresh_max_age,
        httponly=True,
    )
    if device_result.raw_token:
        _set_cookie(
            response,
            settings.DEVICE_COOKIE_NAME,
            device_result.raw_token,
            settings.REMEMBER_SESSION_EXPIRE_DAYS * 86400,
            httponly=True,
        )
    return AuthResponse(
        message=translate("message.auth.login"),
        user=AuthenticatedUser.model_validate(user),
        session=CurrentSession.model_validate(user_session),
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    dependencies=[Depends(verify_csrf)],
)
def refresh_session(
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
) -> AuthResponse:
    user_session, access_token, refresh_token = (
        auth_service.session_service.refresh(
            database, request.cookies.get(settings.REFRESH_COOKIE_NAME)
        )
    )
    _set_cookie(
        response,
        settings.SESSION_COOKIE_NAME,
        access_token,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    refresh_expires_at = ensure_utc(user_session.refresh_expires_at) or utc_now()
    remaining_seconds = max(
        1, int((refresh_expires_at - utc_now()).total_seconds())
    )
    _set_cookie(
        response,
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        remaining_seconds,
        httponly=True,
    )
    return AuthResponse(
        message=translate("message.auth.refreshed"),
        user=AuthenticatedUser.model_validate(user_session.user),
        session=CurrentSession.model_validate(user_session),
    )


@router.get("/me", response_model=AuthResponse)
def me(
    user_session: UserSession = Depends(get_current_session),
) -> AuthResponse:
    return AuthResponse(
        message=translate("message.auth.valid_session"),
        user=AuthenticatedUser.model_validate(user_session.user),
        session=CurrentSession.model_validate(user_session),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(verify_csrf)],
)
def logout(
    request: Request,
    response: Response,
    user_session: UserSession = Depends(get_current_session),
    database: Session = Depends(get_db),
) -> LogoutResponse:
    revoked = session_repository.revoke(database, user_session, utc_now())
    audit_service.record(
        database,
        "LOGOUT",
        user_id=user_session.user_id,
        session_id=user_session.id,
        ip_address=_client_ip(request),
    )
    database.commit()
    _delete_session_cookie(response)
    return LogoutResponse(
        message=translate("message.auth.logout"),
        revoked_sessions=1 if revoked else 0,
    )


@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    dependencies=[Depends(verify_csrf)],
)
def logout_all(
    request: Request,
    response: Response,
    user_session: UserSession = Depends(get_current_session),
    database: Session = Depends(get_db),
) -> LogoutResponse:
    count = session_repository.revoke_all_for_user(
        database, user_session.user_id, utc_now()
    )
    audit_service.record(
        database,
        "LOGOUT_ALL",
        user_id=user_session.user_id,
        session_id=user_session.id,
        ip_address=_client_ip(request),
        event_metadata={"revoked_sessions": count},
    )
    database.commit()
    _delete_session_cookie(response)
    return LogoutResponse(
        message=translate("message.auth.logout_all"), revoked_sessions=count
    )


@router.post(
    "/change-password",
    response_model=LogoutResponse,
    dependencies=[Depends(verify_csrf)],
)
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    user_session: UserSession = Depends(get_current_session),
    database: Session = Depends(get_db),
) -> LogoutResponse:
    auth_service.change_password(
        database,
        user_session.user,
        user_session,
        data,
        _client_ip(request),
    )
    return LogoutResponse(message=translate("message.auth.password_changed"))


def _mask_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    if "." in ip_address:
        parts = ip_address.split(".")
        return ".".join(parts[:2] + ["xxx", "xxx"]) if len(parts) == 4 else "oculta"
    return f"{ip_address.split(':', 2)[0]}:xxxx:xxxx"


@router.get("/sessions", response_model=SessionsResponse)
def list_sessions(
    current: UserSession = Depends(get_current_session),
    database: Session = Depends(get_db),
) -> SessionsResponse:
    sessions = session_repository.list_for_user(database, current.user_id)
    return SessionsResponse(
        sessions=[
            SessionSummary(
                id=item.id,
                device_name=item.device.device_name if item.device else None,
                browser=item.device.browser if item.device else None,
                operating_system=item.device.operating_system if item.device else None,
                device_type=item.device.device_type if item.device else None,
                ip_address=_mask_ip(item.ip_address),
                created_at=item.created_at,
                last_activity_at=item.last_activity_at,
                expires_at=item.expires_at,
                is_current=item.id == current.id,
            )
            for item in sessions
        ]
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=LogoutResponse,
    dependencies=[Depends(verify_csrf)],
)
def revoke_session(
    session_id: UUID,
    request: Request,
    response: Response,
    current: UserSession = Depends(get_current_session),
    database: Session = Depends(get_db),
) -> LogoutResponse:
    target = session_repository.get_by_id_for_user(
        database, session_id, current.user_id
    )
    if not target:
        raise ApplicationError(
            "SESSION_NOT_FOUND", "La sesión solicitada no existe.", 404
        )
    revoked = session_repository.revoke(database, target, utc_now())
    audit_service.record(
        database,
        "SESSION_REVOKED",
        user_id=current.user_id,
        session_id=current.id,
        resource_type="session",
        resource_id=str(target.id),
        ip_address=_client_ip(request),
    )
    database.commit()
    if target.id == current.id:
        _delete_session_cookie(response)
    return LogoutResponse(
        message=translate("message.auth.session_revoked"),
        revoked_sessions=1 if revoked else 0,
    )
