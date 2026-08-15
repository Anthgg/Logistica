from uuid import uuid4

from sqlalchemy import select

from app.core.config import settings
from app.core.security import verify_password
from app.models.audit_log import AuditLog
from app.models.session import UserSession
from app.models.user import User


def csrf_headers(client) -> dict[str, str]:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def credentials() -> tuple[str, str]:
    return f"auth-{uuid4().hex}@example.com", "ContraseñaSegura2026"


def register(client, email: str, password: str, headers: dict[str, str]):
    return client.post(
        "/api/auth/register",
        headers=headers,
        json={
            "full_name": "Usuario de prueba",
            "email": email.upper(),
            "password": password,
            "password_confirmation": password,
            "accept_terms": True,
        },
    )


def login(client, email: str, password: str, headers: dict[str, str]):
    return client.post(
        "/api/auth/login",
        headers=headers,
        json={"email": email, "password": password, "remember_me": False},
    )


def test_register_normalizes_and_hashes_password(client, database) -> None:
    email, password = credentials()
    response = register(client, email, password, csrf_headers(client))
    assert response.status_code == 201
    assert "password_hash" not in response.text
    user = database.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.email == email.lower()
    assert user.password_hash != password
    assert verify_password(password, user.password_hash)
    assert database.scalar(
        select(AuditLog).where(
            AuditLog.user_id == user.id, AuditLog.event_type == "USER_REGISTERED"
        )
    )


def test_duplicate_and_invalid_registration(client) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    assert register(client, email, password, headers).status_code == 201
    duplicate = register(client, email, password, headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    weak = register(client, f"weak-{email}", "short", headers)
    assert weak.status_code == 422
    mismatch = client.post(
        "/api/auth/register",
        headers=headers,
        json={
            "full_name": "Test",
            "email": f"mismatch-{email}",
            "password": password,
            "password_confirmation": f"{password}x",
            "accept_terms": True,
        },
    )
    assert mismatch.status_code == 422


def test_login_me_sessions_logout(client, database) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    register(client, email, password, headers)
    response = login(client, email, password, headers)
    assert response.status_code == 200
    assert settings.SESSION_COOKIE_NAME in client.cookies
    assert settings.REFRESH_COOKIE_NAME in client.cookies
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "token_hash" not in response.text

    user = database.scalar(select(User).where(User.email == email))
    stored_session = database.scalar(
        select(UserSession).where(UserSession.user_id == user.id)
    )
    assert stored_session is not None
    assert stored_session.token_hash not in client.cookies.values()
    assert stored_session.refresh_token_hash not in client.cookies.values()
    assert stored_session.device_id is not None

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email
    sessions = client.get("/api/auth/sessions")
    assert sessions.status_code == 200
    assert sessions.json()["sessions"][0]["is_current"] is True
    assert "token_hash" not in sessions.text

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    database.refresh(stored_session)
    assert stored_session.revoked_at is not None
    assert client.get("/api/auth/me").status_code == 401


def test_refresh_rotates_both_jwt_cookies(client, database) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    register(client, email, password, headers)
    login(client, email, password, headers)
    old_access = client.cookies[settings.SESSION_COOKIE_NAME]
    old_refresh = client.cookies[settings.REFRESH_COOKIE_NAME]

    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 200
    assert client.cookies[settings.SESSION_COOKIE_NAME] != old_access
    assert client.cookies[settings.REFRESH_COOKIE_NAME] != old_refresh
    user = database.scalar(select(User).where(User.email == email))
    user_session = database.scalar(
        select(UserSession).where(UserSession.user_id == user.id)
    )
    assert user_session.previous_refresh_token_hash is not None
    assert "refresh_token" not in response.text


def test_reusing_previous_refresh_revokes_session(client, database) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    register(client, email, password, headers)
    login(client, email, password, headers)
    stolen_refresh = client.cookies[settings.REFRESH_COOKIE_NAME]
    assert client.post("/api/auth/refresh", headers=headers).status_code == 200

    client.cookies.set(settings.REFRESH_COOKIE_NAME, stolen_refresh)
    reused = client.post("/api/auth/refresh", headers=headers)
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    user = database.scalar(select(User).where(User.email == email))
    user_session = database.scalar(
        select(UserSession).where(UserSession.user_id == user.id)
    )
    database.refresh(user_session)
    assert user_session.revoked_at is not None


def test_invalid_login_increments_attempts_and_is_generic(client, database) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    register(client, email, password, headers)
    response = login(client, email, "incorrecta", headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    user = database.scalar(select(User).where(User.email == email))
    database.refresh(user)
    assert user.failed_login_attempts == 1
    assert database.scalar(
        select(AuditLog).where(
            AuditLog.user_id == user.id, AuditLog.event_type == "LOGIN_FAILED"
        )
    )


def test_change_password_and_logout_all(client, database) -> None:
    email, password = credentials()
    headers = csrf_headers(client)
    register(client, email, password, headers)
    login(client, email, password, headers)
    user = database.scalar(select(User).where(User.email == email))
    old_hash = user.password_hash
    changed = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": password,
            "new_password": "NuevaContraseñaSegura2026",
            "new_password_confirmation": "NuevaContraseñaSegura2026",
            "logout_other_sessions": True,
        },
    )
    assert changed.status_code == 200
    database.refresh(user)
    assert user.password_hash != old_hash
    assert verify_password("NuevaContraseñaSegura2026", user.password_hash)
    assert client.post("/api/auth/logout-all", headers=headers).status_code == 200


def test_csrf_and_missing_session_are_rejected(client) -> None:
    email, password = credentials()
    no_csrf = client.post(
        "/api/auth/login",
        json={"email": email, "password": password, "remember_me": False},
    )
    assert no_csrf.status_code == 403
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_REQUIRED"
    assert "DATABASE_URL" not in response.text
    assert response.headers["X-Request-ID"]
