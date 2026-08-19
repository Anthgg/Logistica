import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-never-used-2026")


class PasswordValidationError(ValueError):
    pass


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Comprueba una contraseña contra su hash. Un hash irreconocible es un fallo.

    Un hash que pwdlib no sabe interpretar significa que esa credencial no puede
    verificarse, y eso es exactamente lo mismo que una contraseña incorrecta: no hay
    prueba de identidad. Devolverlo como ``False`` mantiene un único contrato para
    quien llama, en lugar de obligar a cada consumidor a conocer las excepciones de
    la librería.

    Hasta ahora ``UnknownHashError`` escapaba —hereda de ``PwdlibError``, no de
    ``ValueError``— y el intento de acceso terminaba en 500. Como un usuario
    inexistente devuelve 401, la diferencia de respuesta delataba qué correos existen
    con un hash heredado inválido.

    Se captura la excepción concreta y no su base: ``HasherNotAvailable``, la otra
    hija de ``PwdlibError``, indica que falta el backend de hashing. Eso es un fallo
    de configuración del servicio y debe propagarse, no disfrazarse de credencial
    incorrecta para todo el mundo.
    """
    try:
        return password_hasher.verify(password, password_hash)
    except (ValueError, TypeError, UnknownHashError):
        return False


def validate_password_strength(
    password: str, email: str, minimum_length: int = 10
) -> None:
    if not password.strip():
        raise PasswordValidationError("La contraseña no puede contener solo espacios.")
    if len(password) < minimum_length:
        raise PasswordValidationError(
            f"La contraseña debe tener al menos {minimum_length} caracteres."
        )
    if len(password) > 128:
        raise PasswordValidationError("La contraseña no puede superar 128 caracteres.")
    if secure_compare(password.casefold(), email.strip().casefold()):
        raise PasswordValidationError("La contraseña no puede ser igual al correo.")


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, session_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: UUID, session_id: UUID, expires_at: datetime
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "sid", "type", "jti", "iat", "exp"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("Token JWT inválido.") from exc
    if payload.get("type") != expected_type:
        raise ValueError("Tipo de token JWT inválido.")
    return payload


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


def hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def secure_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
