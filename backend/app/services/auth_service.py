from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    PasswordValidationError,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.database.base import utc_now
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import DuplicateEmailError, UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.user import UserCreateInternal
from app.services.audit_service import AuditService
from app.services.device_service import DeviceResult, DeviceService
from app.services.session_service import SessionService


class AuthService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.sessions = SessionRepository()
        self.audit = AuditService()
        self.devices = DeviceService()
        self.session_service = SessionService()

    def register(
        self,
        database: Session,
        data: RegisterRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        email = self.users.normalize_email(str(data.email))
        if data.password != data.password_confirmation:
            raise ApplicationError("PASSWORD_MISMATCH", "Las contraseñas no coinciden.", 422)
        if not data.accept_terms:
            raise ApplicationError(
                "TERMS_REQUIRED", "Debe aceptar los términos para registrarse.", 422
            )
        self._validate_password(data.password, email)
        if self.users.get_by_email(database, email):
            self.audit.record(
                database,
                "REGISTER_DUPLICATE_EMAIL",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            database.commit()
            raise ApplicationError(
                "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado.", 409
            )
        try:
            user = self.users.create(
                database,
                UserCreateInternal(
                    email=email,
                    password_hash=hash_password(data.password),
                    full_name=data.full_name.strip(),
                    role="user",
                ),
            )
            self.audit.record(
                database,
                "USER_REGISTERED",
                user_id=user.id,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            database.commit()
            database.refresh(user)
            return user
        except DuplicateEmailError as exc:
            raise ApplicationError(
                "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado.", 409
            ) from exc
        except Exception:
            database.rollback()
            raise

    def login(
        self,
        database: Session,
        data: LoginRequest,
        raw_device_token: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[User, UserSession, str, str, DeviceResult]:
        email = self.users.normalize_email(str(data.email))
        user = self.users.get_by_email(database, email)
        if not user:
            verify_password(data.password, DUMMY_PASSWORD_HASH)
            self.audit.record(
                database, "LOGIN_FAILED", ip_address=ip_address, user_agent=user_agent
            )
            database.commit()
            raise self._invalid_credentials()
        now = utc_now()
        if not user.is_active:
            self.audit.record(
                database, "LOGIN_BLOCKED_USER", user_id=user.id, ip_address=ip_address
            )
            database.commit()
            raise ApplicationError("ACCOUNT_DISABLED", "La cuenta está desactivada.", 403)
        if user.locked_until and user.locked_until > now:
            raise ApplicationError(
                "ACCOUNT_TEMPORARILY_LOCKED",
                "La cuenta está bloqueada temporalmente.",
                423,
            )
        if not verify_password(data.password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
                self.audit.record(
                    database,
                    "ACCOUNT_TEMPORARILY_LOCKED",
                    user_id=user.id,
                    ip_address=ip_address,
                )
            self.audit.record(
                database,
                "LOGIN_FAILED",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            database.commit()
            raise self._invalid_credentials()

        device_result = self.devices.recognize(
            database, user, raw_device_token, user_agent
        )
        if device_result.device.is_blocked:
            self.audit.record(
                database,
                "LOGIN_BLOCKED_DEVICE",
                user_id=user.id,
                ip_address=ip_address,
            )
            database.commit()
            raise ApplicationError("DEVICE_BLOCKED", "El dispositivo está bloqueado.", 403)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        user_session, raw_session_token, raw_refresh_token = self.session_service.create(
            database,
            user,
            device_result.device,
            ip_address,
            user_agent,
            data.remember_me,
        )
        self.audit.record(
            database,
            "LOGIN_SUCCESS",
            user_id=user.id,
            session_id=user_session.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        database.commit()
        return user, user_session, raw_session_token, raw_refresh_token, device_result

    def change_password(
        self,
        database: Session,
        user: User,
        current_session: UserSession,
        data: ChangePasswordRequest,
        ip_address: str | None,
    ) -> None:
        if data.new_password != data.new_password_confirmation:
            raise ApplicationError(
                "PASSWORD_MISMATCH", "Las contraseñas nuevas no coinciden.", 422
            )
        if not verify_password(data.current_password, user.password_hash):
            raise ApplicationError(
                "CURRENT_PASSWORD_INCORRECT",
                "La contraseña actual es incorrecta.",
                400,
            )
        if verify_password(data.new_password, user.password_hash):
            raise ApplicationError(
                "WEAK_PASSWORD",
                "La nueva contraseña debe ser diferente de la actual.",
                422,
            )
        self._validate_password(data.new_password, user.email)
        user.password_hash = hash_password(data.new_password)
        if data.logout_other_sessions:
            self.sessions.revoke_all_for_user(
                database, user.id, utc_now(), except_session_id=current_session.id
            )
        self.audit.record(
            database,
            "PASSWORD_CHANGED",
            user_id=user.id,
            session_id=current_session.id,
            ip_address=ip_address,
        )
        database.commit()

    @staticmethod
    def _validate_password(password: str, email: str) -> None:
        try:
            validate_password_strength(password, email, settings.PASSWORD_MIN_LENGTH)
        except PasswordValidationError as exc:
            raise ApplicationError("WEAK_PASSWORD", str(exc), 422) from exc

    @staticmethod
    def _invalid_credentials() -> ApplicationError:
        return ApplicationError(
            "INVALID_CREDENTIALS", "Correo o contraseña incorrectos.", 401
        )
