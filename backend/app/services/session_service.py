from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_refresh_token,
    hash_session_token,
)
from app.database.base import utc_now
from app.models.device import Device
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.services.audit_service import AuditService


class SessionService:
    def __init__(self) -> None:
        self.repository = SessionRepository()
        self.audit = AuditService()

    def create(
        self,
        database: Session,
        user: User,
        device: Device,
        ip_address: str | None,
        user_agent: str | None,
        remember_me: bool,
    ) -> tuple[UserSession, str, str]:
        now = utc_now()
        refresh_duration = (
            timedelta(days=settings.REMEMBER_SESSION_EXPIRE_DAYS)
            if remember_me
            else timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
        )
        refresh_expires_at = now + refresh_duration
        user_session = self.repository.create(
            database,
            user_id=user.id,
            device_id=device.id,
            token_hash=f"pending-{uuid4()}",
            refresh_token_hash=f"pending-{uuid4()}",
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            refresh_expires_at=refresh_expires_at,
            authentication_level="traditional",
            created_by_login=True,
        )
        access_token = create_access_token(user.id, user_session.id)
        refresh_token = create_refresh_token(
            user.id, user_session.id, refresh_expires_at
        )
        user_session.token_hash = hash_session_token(access_token)
        user_session.refresh_token_hash = hash_refresh_token(refresh_token)
        database.flush()
        return user_session, access_token, refresh_token

    def authenticate(self, database: Session, raw_token: str | None) -> UserSession:
        if not raw_token:
            raise ApplicationError(
                "SESSION_REQUIRED", "Se requiere una sesión válida.", 401
            )
        try:
            claims = decode_jwt_token(raw_token, "access")
        except ValueError as exc:
            raise ApplicationError("INVALID_SESSION", "La sesión no es válida.", 401) from exc
        user_session = self.repository.get_by_token_hash(database, hash_session_token(raw_token))
        if not user_session:
            raise ApplicationError("INVALID_SESSION", "La sesión no es válida.", 401)
        if (
            str(user_session.id) != claims["sid"]
            or str(user_session.user_id) != claims["sub"]
        ):
            raise ApplicationError("INVALID_SESSION", "La sesión no es válida.", 401)
        if user_session.revoked_at:
            raise ApplicationError("SESSION_REVOKED", "La sesión fue revocada.", 401)

        now = utc_now()
        if user_session.expires_at <= now:
            user_session.revoked_at = now
            self.audit.record(
                database,
                "SESSION_EXPIRED",
                user_id=user_session.user_id,
                session_id=user_session.id,
            )
            database.commit()
            raise ApplicationError("SESSION_EXPIRED", "La sesión expiró.", 401)
        idle_limit = timedelta(minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES)
        if user_session.last_activity_at + idle_limit <= now:
            user_session.revoked_at = now
            self.audit.record(
                database,
                "SESSION_IDLE_TIMEOUT",
                user_id=user_session.user_id,
                session_id=user_session.id,
            )
            database.commit()
            raise ApplicationError(
                "SESSION_EXPIRED", "La sesión expiró por inactividad.", 401
            )
        if not user_session.user.is_active:
            raise ApplicationError("ACCOUNT_DISABLED", "La cuenta está desactivada.", 403)
        if user_session.device and user_session.device.is_blocked:
            raise ApplicationError("DEVICE_BLOCKED", "El dispositivo está bloqueado.", 403)

        update_interval = timedelta(seconds=settings.SESSION_ACTIVITY_UPDATE_SECONDS)
        if user_session.last_activity_at + update_interval <= now:
            user_session.last_activity_at = now
            database.commit()
        return user_session

    def refresh(
        self, database: Session, raw_refresh_token: str | None
    ) -> tuple[UserSession, str, str]:
        if not raw_refresh_token:
            raise ApplicationError(
                "REFRESH_TOKEN_REQUIRED", "Se requiere un refresh token.", 401
            )
        try:
            claims = decode_jwt_token(raw_refresh_token, "refresh")
        except ValueError as exc:
            raise ApplicationError(
                "INVALID_REFRESH_TOKEN", "El refresh token no es válido.", 401
            ) from exc
        refresh_hash = hash_refresh_token(raw_refresh_token)
        user_session, reused = self.repository.get_by_refresh_hash(
            database, refresh_hash
        )
        if not user_session:
            raise ApplicationError(
                "INVALID_REFRESH_TOKEN", "El refresh token no es válido.", 401
            )
        now = utc_now()
        if reused:
            user_session.revoked_at = now
            self.audit.record(
                database,
                "REFRESH_TOKEN_REUSE_DETECTED",
                user_id=user_session.user_id,
                session_id=user_session.id,
            )
            database.commit()
            raise ApplicationError(
                "REFRESH_TOKEN_REUSED",
                "Se detectó reutilización del refresh token. La sesión fue revocada.",
                401,
            )
        if (
            user_session.revoked_at
            or not user_session.refresh_expires_at
            or user_session.refresh_expires_at <= now
        ):
            raise ApplicationError(
                "REFRESH_TOKEN_EXPIRED", "El refresh token expiró.", 401
            )
        if (
            str(user_session.id) != claims["sid"]
            or str(user_session.user_id) != claims["sub"]
        ):
            raise ApplicationError(
                "INVALID_REFRESH_TOKEN", "El refresh token no es válido.", 401
            )
        if not user_session.user.is_active:
            raise ApplicationError("ACCOUNT_DISABLED", "La cuenta está desactivada.", 403)

        new_access = create_access_token(user_session.user_id, user_session.id)
        new_refresh = create_refresh_token(
            user_session.user_id,
            user_session.id,
            user_session.refresh_expires_at,
        )
        user_session.token_hash = hash_session_token(new_access)
        user_session.previous_refresh_token_hash = user_session.refresh_token_hash
        user_session.refresh_token_hash = hash_refresh_token(new_refresh)
        user_session.expires_at = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        user_session.last_activity_at = now
        self.audit.record(
            database,
            "REFRESH_TOKEN_ROTATED",
            user_id=user_session.user_id,
            session_id=user_session.id,
        )
        database.commit()
        return user_session, new_access, new_refresh
