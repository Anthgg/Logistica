import re
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import Response

from app.api.routes.auth import csrf
from app.core.config import settings
from app.database.base import utc_now
from app.core.security import (
    PasswordValidationError,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    generate_device_token,
    generate_session_token,
    hash_device_token,
    hash_password,
    hash_session_token,
    secure_compare,
    validate_password_strength,
    verify_password,
)


def test_passwords_use_argon2id() -> None:
    password_hash = hash_password("ContraseñaSegura2026")
    assert password_hash.startswith("$argon2id$")
    assert verify_password("ContraseñaSegura2026", password_hash)
    assert not verify_password("incorrecta", password_hash)


@pytest.mark.parametrize(
    "password,email",
    [
        ("corta", "user@example.com"),
        ("          ", "user@example.com"),
        ("user@example.com", "user@example.com"),
        ("a" * 129, "user@example.com"),
    ],
)
def test_weak_passwords_are_rejected(password: str, email: str) -> None:
    with pytest.raises(PasswordValidationError):
        validate_password_strength(password, email)


def test_tokens_have_entropy_and_only_sha256_is_stored() -> None:
    session_token = generate_session_token()
    device_token = generate_device_token()
    assert len(session_token) >= 43
    assert len(device_token) >= 43
    assert re.fullmatch(r"[0-9a-f]{64}", hash_session_token(session_token))
    assert re.fullmatch(r"[0-9a-f]{64}", hash_device_token(device_token))
    assert session_token != hash_session_token(session_token)
    assert secure_compare("same", "same")


def test_access_and_refresh_are_signed_jwt() -> None:
    user_id, session_id = uuid4(), uuid4()
    access = create_access_token(user_id, session_id)
    refresh = create_refresh_token(
        user_id, session_id, utc_now() + timedelta(hours=8)
    )
    assert access.count(".") == 2
    assert refresh.count(".") == 2
    assert decode_jwt_token(access, "access")["sid"] == str(session_id)
    assert decode_jwt_token(refresh, "refresh")["sub"] == str(user_id)


def test_csrf_cookie_supports_cross_site_frontends(monkeypatch) -> None:
    monkeypatch.setattr(settings, "SESSION_COOKIE_SAMESITE", "none")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    response = Response()

    csrf(response)

    set_cookie = response.headers["set-cookie"].lower()
    assert "samesite=none" in set_cookie
    assert "secure" in set_cookie
