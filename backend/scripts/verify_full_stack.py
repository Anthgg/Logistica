from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Mapping, cast
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx
from PIL import Image
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


class FullStackVerificationError(RuntimeError):
    """Raised when an integration contract does not hold."""


def _object(response: httpx.Response) -> Mapping[str, object]:
    payload = response.json()
    if not isinstance(payload, dict):
        raise FullStackVerificationError(
            f"{response.request.url.path} no devolvió un objeto JSON."
        )
    return cast(Mapping[str, object], payload)


def _expect(
    response: httpx.Response,
    expected: Iterable[int],
    name: str,
) -> None:
    accepted = set(expected)
    if response.status_code not in accepted:
        raise FullStackVerificationError(
            f"{name} respondió HTTP {response.status_code}; "
            f"se esperaba {sorted(accepted)}."
        )


def _csrf(client: httpx.Client) -> str:
    response = client.get("/auth/csrf")
    _expect(response, {200}, "CSRF")
    value = _object(response).get("csrf_token")
    if not isinstance(value, str) or not value:
        raise FullStackVerificationError("La API no entregó un token CSRF.")
    return value


def _cookie_checks(
    response: httpx.Response,
    *,
    secure_expected: bool,
) -> None:
    headers = response.headers.get_list("set-cookie")
    for cookie in (
        settings.SESSION_COOKIE_NAME,
        settings.REFRESH_COOKIE_NAME,
    ):
        matching = [
            header.casefold()
            for header in headers
            if header.casefold().startswith(cookie + "=")
        ]
        if not matching or "httponly" not in matching[0]:
            raise FullStackVerificationError(
                f"La cookie {cookie} no está protegida con HttpOnly."
            )
        if secure_expected and "secure" not in matching[0]:
            raise FullStackVerificationError(
                f"La cookie {cookie} no está protegida con Secure."
            )
        if not secure_expected and "secure" in matching[0]:
            raise FullStackVerificationError(
                f"La cookie {cookie} usa Secure en el entorno HTTP local."
            )
        if (
            f"samesite={settings.SESSION_COOKIE_SAMESITE}"
            not in matching[0]
            or "path=/" not in matching[0]
            or "max-age=" not in matching[0]
        ):
            raise FullStackVerificationError(
                f"La cookie {cookie} no declara SameSite, Path y Max-Age."
            )


def _jpeg() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color=(127, 127, 127)).save(
        buffer,
        format="JPEG",
    )
    return buffer.getvalue()


def _identifier(payload: Mapping[str, object], field: str = "id") -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise FullStackVerificationError(
            f"La respuesta no contiene el identificador {field}."
        )
    return value


def _research_flow(
    client: httpx.Client,
    engine: Engine,
    *,
    user_id: str,
    password: str,
    identifier: str,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    csrf_token = _csrf(client)
    client.headers["X-CSRF-Token"] = csrf_token
    participant_response = client.post(
        "/research/participants",
        json={"linked_user_id": user_id},
    )
    _expect(participant_response, {201}, "Participante sintético")
    participant_id = _identifier(_object(participant_response))
    consent = client.post(
        "/research/consent",
        json={
            "participant_id": participant_id,
            "consent_version": "integration-test-v1",
            "accepted": True,
        },
    )
    _expect(consent, {201}, "Consentimiento sintético")
    started = client.post(
        "/research/sessions/start",
        json={
            "participant_id": participant_id,
            "scenario": "register_shipment",
            "expected_duration_minutes": 10,
            "client_timezone": "America/Lima",
            "client_timezone_offset_minutes": -300,
            "client_language": "es-PE",
            "screen_width": 1280,
            "screen_height": 720,
            "screen_pixel_ratio": 1.0,
            "browser": "integration-test-client",
            "operating_system": "container",
            "device_type": "desktop",
            "collector_version": "integration-test-v1",
        },
    )
    _expect(started, {201}, "Sesión experimental")
    session_value = _object(started).get("session")
    if not isinstance(session_value, dict):
        raise FullStackVerificationError(
            "La sesión experimental no contiene su objeto session."
        )
    session_id = _identifier(cast(Mapping[str, object], session_value))
    now = datetime.now(timezone.utc)
    capture = client.post(
        f"/research/sessions/{session_id}/face-captures",
        data={
            "captured_at": now.isoformat(),
            "sequence_number": "1",
            "width": "64",
            "height": "64",
            "visibility_state": "visible",
            "client_timezone_offset": "-300",
            "capture_source": "webcam",
            "camera_facing_mode": "user",
        },
        files={
            "image": (
                f"integration-test-{identifier}.jpg",
                _jpeg(),
                "image/jpeg",
            )
        },
    )
    _expect(capture, {201}, "Captura facial sintética")
    capture_id = _identifier(_object(capture))
    batch_start = now + timedelta(milliseconds=100)
    behavior = client.post(
        f"/research/sessions/{session_id}/behavior-batches",
        json={
            "batch_id": str(uuid4()),
            "sequence_number": 1,
            "started_at": batch_start.isoformat(),
            "ended_at": (batch_start + timedelta(seconds=3)).isoformat(),
            "visibility_state": "visible",
            "client_timezone_offset_minutes": -300,
            "dropped_event_count": 0,
            "collector_error_count": 0,
            "events": [
                {
                    "type": "keyboard",
                    "event": "timing",
                    "category": "alphanumeric",
                    "dwell_time_ms": 85,
                    "flight_time_ms": 120,
                    "timestamp": batch_start.isoformat(),
                    "sequence_index": 1,
                },
                {
                    "type": "mouse",
                    "event": "move",
                    "normalized_x": 0.42,
                    "normalized_y": 0.61,
                    "velocity": 10,
                    "timestamp": batch_start.isoformat(),
                    "sequence_index": 2,
                },
            ],
        },
    )
    _expect(behavior, {201}, "Lote conductual sintético")
    results.extend(
        [
            CheckResult(
                "experimental_session",
                "passed",
                "consent and active session",
            ),
            CheckResult("facial_capture", "passed", "synthetic JPEG"),
            CheckResult("behavioral_batch", "passed", "synthetic events"),
        ]
    )
    evaluation = client.post(
        "/continuous-auth/evaluate",
        json={
            "experimental_session_id": session_id,
            "facial_capture_id": capture_id,
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    model_blocker: str | None = None
    if evaluation.status_code == 200:
        results.append(
            CheckResult(
                "continuous_auth_inference",
                "passed",
                "approved runtimes responded",
            )
        )
    elif evaluation.status_code in {409, 503}:
        model_blocker = (
            "La integración de inferencia quedó bloqueada con HTTP "
            f"{evaluation.status_code}; faltan fixtures/modelos aprobados."
        )
        results.append(
            CheckResult(
                "continuous_auth_inference",
                "blocked",
                model_blocker,
            )
        )
    else:
        _expect(evaluation, {200}, "Evaluación continua")
    risk_status = client.get("/continuous-auth/status")
    _expect(risk_status, {200}, "Estado de riesgo")
    reverified = client.post(
        "/continuous-auth/reverify",
        json={"password": password},
    )
    _expect(reverified, {200}, "Reverificación")
    results.extend(
        [
            CheckResult("risk_status", "passed", "HTTP 200"),
            CheckResult("reverification", "passed", "password verified"),
        ]
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE experimental_sessions "
                "SET started_at = :started_at WHERE id = CAST(:id AS uuid)"
            ),
            {
                "started_at": datetime.now(timezone.utc)
                - timedelta(seconds=20),
                "id": session_id,
            },
        )
    finished = client.post(
        f"/research/sessions/{session_id}/finish",
        json={
            "client_ended_at": datetime.now(timezone.utc).isoformat(),
            "client_error_count": 0,
        },
    )
    _expect(finished, {200}, "Finalización experimental")
    results.append(
        CheckResult("experimental_finish", "passed", "HTTP 200")
    )
    return results


def _database_checks() -> tuple[Engine, list[CheckResult]]:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    results: list[CheckResult] = []
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        results.append(CheckResult("postgres", "passed", "SELECT 1"))
        inspector = inspect(connection)
        if not inspector.has_table("alembic_version"):
            raise FullStackVerificationError(
                "No existe alembic_version; faltan migraciones."
            )
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        results.append(
            CheckResult("migrations", "passed", str(version))
        )
    return engine, results


def _cleanup(engine: Engine, email: str) -> None:
    if not email.startswith("integration-test-") or not email.endswith(
        "@example.com"
    ):
        raise FullStackVerificationError(
            "La limpieza rechazó un identificador fuera del prefijo permitido."
        )
    capture_paths: list[str] = []
    with engine.begin() as connection:
        user_id = connection.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).scalar_one_or_none()
        if user_id is None:
            return
        capture_paths = [
            str(value)
            for value in connection.execute(
                text(
                    "SELECT fc.storage_path "
                    "FROM facial_captures fc "
                    "JOIN experimental_sessions es "
                    "ON es.id = fc.experimental_session_id "
                    "WHERE es.user_id = :user_id"
                ),
                {"user_id": user_id},
            ).scalars()
        ]
        connection.execute(
            text("DELETE FROM audit_logs WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        connection.execute(
            text(
                "DELETE FROM experimental_sessions "
                "WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        )
        connection.execute(
            text(
                "DELETE FROM consent_records WHERE participant_id IN "
                "(SELECT id FROM research_participants "
                "WHERE linked_user_id = :user_id)"
            ),
            {"user_id": user_id},
        )
        connection.execute(
            text(
                "DELETE FROM research_participants "
                "WHERE linked_user_id = :user_id"
            ),
            {"user_id": user_id},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
    storage_root = Path(settings.CAPTURE_LOCAL_PATH).resolve()
    for value in capture_paths:
        candidate = (storage_root / value).resolve()
        try:
            candidate.relative_to(storage_root)
        except ValueError as exc:
            raise FullStackVerificationError(
                "La limpieza encontró una captura fuera del directorio permitido."
            ) from exc
        candidate.unlink(missing_ok=True)
        try:
            candidate.parent.rmdir()
        except OSError:
            continue


def verify(
    *,
    api_url: str,
    frontend_url: str,
    frontend_origin: str,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    engine, database_results = _database_checks()
    results.extend(database_results)
    identifier = uuid4().hex
    email = f"integration-test-{identifier}@example.com"
    password = f"Integration-{identifier}-Aa9!"
    headers = {
        "Origin": frontend_origin.rstrip("/"),
        "User-Agent": "continuous-authentication-integration-verifier/1.0",
        "Accept-Language": "es",
    }
    try:
        frontend = httpx.get(frontend_url, timeout=15)
        _expect(frontend, {200}, "Frontend")
        results.append(
            CheckResult("frontend", "passed", "HTTP 200")
        )
        service_root = api_url.rstrip("/").removesuffix("/api")
        docs = httpx.get(f"{service_root}/docs", timeout=15)
        _expect(docs, {200, 404}, "Swagger")
        results.append(
            CheckResult(
                "swagger",
                "passed",
                "available" if docs.status_code == 200 else "disabled",
            )
        )
        openapi = httpx.get(f"{service_root}/openapi.json", timeout=15)
        _expect(openapi, {200}, "OpenAPI")
        paths = _object(openapi).get("paths")
        if not isinstance(paths, dict):
            raise FullStackVerificationError(
                "OpenAPI no contiene rutas."
            )
        expected_routes = {
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/refresh",
            "/api/auth/me",
            "/api/auth/logout",
            "/api/dashboard/summary",
            "/api/clients",
            "/api/shipments",
            "/api/inventory",
            "/api/research/sessions/start",
            "/api/research/sessions/{session_id}/face-captures",
            "/api/research/sessions/{session_id}/behavior-batches",
            "/api/continuous-auth/evaluate",
            "/api/continuous-auth/reverify",
            "/api/models/status",
        }
        missing_routes = expected_routes - set(paths)
        if missing_routes:
            raise FullStackVerificationError(
                "Faltan rutas: " + ", ".join(sorted(missing_routes))
            )
        results.append(
            CheckResult("openapi_contract", "passed", "critical routes")
        )
        with httpx.Client(
            base_url=api_url.rstrip("/"),
            headers=headers,
            follow_redirects=True,
            timeout=20,
        ) as client:
            health = client.get("/health")
            _expect(health, {200}, "Backend health")
            results.append(
                CheckResult("backend_health", "passed", "database connected")
            )
            expected_origin = frontend_origin.rstrip("/")
            if (
                health.headers.get("access-control-allow-origin")
                != expected_origin
                or health.headers.get("access-control-allow-credentials")
                != "true"
            ):
                raise FullStackVerificationError(
                    "CORS no permite exactamente el frontend con credenciales."
                )
            results.append(
                CheckResult("cors", "passed", expected_origin)
            )
            registration = {
                "full_name": f"integration-test-{identifier}",
                "email": email,
                "password": password,
                "password_confirmation": password,
                "accept_terms": True,
            }
            rejected = client.post("/auth/register", json=registration)
            _expect(rejected, {403}, "Registro sin CSRF")
            csrf_token = _csrf(client)
            registered = client.post(
                "/auth/register",
                json=registration,
                headers={"X-CSRF-Token": csrf_token},
            )
            _expect(registered, {201}, "Registro")
            results.append(
                CheckResult("registration", "passed", "synthetic user")
            )
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE users SET role = 'admin' "
                        "WHERE email = :email"
                    ),
                    {"email": email},
                )
            csrf_token = _csrf(client)
            login = client.post(
                "/auth/login",
                json={
                    "email": email,
                    "password": password,
                    "remember_me": True,
                },
                headers={"X-CSRF-Token": csrf_token},
            )
            _expect(login, {200}, "Login")
            _cookie_checks(
                login,
                secure_expected=api_url.casefold().startswith("https://"),
            )
            results.append(
                CheckResult(
                    "login_cookies",
                    "passed",
                    "JWT access and refresh cookies",
                )
            )
            login_payload = _object(login)
            if {
                "access_token",
                "refresh_token",
                "session_token",
            } & set(login_payload):
                raise FullStackVerificationError(
                    "Login expuso tokens fuera de cookies HttpOnly."
                )
            me = client.get("/auth/me")
            _expect(me, {200}, "/auth/me")
            user = _object(me).get("user")
            user_id = (
                str(user.get("id"))
                if isinstance(user, dict) and user.get("id")
                else None
            )
            if user_id is None:
                raise FullStackVerificationError(
                    "/auth/me no identificó al usuario."
                )
            for name, path in (
                ("dashboard", "/dashboard/summary"),
                ("clients", "/clients"),
                ("shipments", "/shipments"),
                ("inventory", "/inventory"),
                ("model_status", "/models/status"),
                ("risk_status", "/continuous-auth/status"),
            ):
                response = client.get(path)
                _expect(response, {200, 409}, name)
                results.append(
                    CheckResult(name, "passed", f"HTTP {response.status_code}")
                )
            research_results = _research_flow(
                client,
                engine,
                user_id=user_id,
                password=password,
                identifier=identifier,
            )
            results.extend(research_results)
            csrf_token = _csrf(client)
            invalid = client.post(
                "/auth/logout",
                headers={"X-CSRF-Token": "invalid-integration-token"},
            )
            _expect(invalid, {403}, "Logout con CSRF inválido")
            refreshed = client.post(
                "/auth/refresh",
                headers={"X-CSRF-Token": csrf_token},
            )
            _expect(refreshed, {200}, "Refresh JWT")
            results.append(
                CheckResult("refresh_rotation", "passed", "HTTP 200")
            )
            csrf_token = _csrf(client)
            logout = client.post(
                "/auth/logout",
                headers={"X-CSRF-Token": csrf_token},
            )
            _expect(logout, {200}, "Logout")
            after_logout = client.get("/auth/me")
            _expect(after_logout, {401}, "Sesión revocada")
            results.append(
                CheckResult("logout_revocation", "passed", "HTTP 401 after logout")
            )
            with engine.connect() as connection:
                audit_count = connection.execute(
                    text(
                        "SELECT COUNT(*) FROM audit_logs "
                        "WHERE user_id = CAST(:user_id AS uuid)"
                    ),
                    {"user_id": user_id},
                ).scalar_one()
            if int(audit_count) < 1:
                raise FullStackVerificationError(
                    "No se encontraron eventos de auditoría."
                )
            results.append(
                CheckResult("audit", "passed", "events persisted")
            )
    finally:
        try:
            _cleanup(engine, email)
        finally:
            engine.dispose()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prueba el stack con datos integration-test-* y los elimina."
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/api",
    )
    parser.add_argument(
        "--frontend-url",
        default="http://localhost:8080",
    )
    parser.add_argument(
        "--frontend-origin",
        help=(
            "Origen público enviado en CORS; por defecto usa --frontend-url. "
            "En Compose suele ser http://localhost:8080."
        ),
    )
    arguments = parser.parse_args()
    try:
        results = verify(
            api_url=arguments.api_url,
            frontend_url=arguments.frontend_url,
            frontend_origin=(
                arguments.frontend_origin or arguments.frontend_url
            ),
        )
    except FullStackVerificationError as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1) from exc
    blocked = [
        result for result in results if result.status == "blocked"
    ]
    print(
        json.dumps(
            {
                "status": "blocked" if blocked else "passed",
                "checks": [asdict(result) for result in results],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if blocked:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
