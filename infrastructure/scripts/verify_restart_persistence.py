from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Mapping, cast
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PersistenceVerificationError(RuntimeError):
    """Raised when state does not survive a backend restart."""


class ApiSession:
    def __init__(self, api_url: str, origin: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.origin = origin.rstrip("/")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        expected: set[int],
    ) -> tuple[int, Mapping[str, object]]:
        body = (
            json.dumps(payload).encode("utf-8")
            if payload is not None
            else None
        )
        request_headers = {
            "Accept": "application/json",
            "Origin": self.origin,
            "User-Agent": "integration-test-persistence-verifier/1.0",
        }
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            f"{self.api_url}/{path.lstrip('/')}",
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=20) as response:
                status = response.status
                raw = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read()
        if status not in expected:
            detail = raw.decode("utf-8", errors="replace")
            raise PersistenceVerificationError(
                f"{method} {path} respondió HTTP {status}: {detail[:400]}"
            )
        if not raw:
            return status, {}
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PersistenceVerificationError(
                f"{method} {path} no devolvió JSON válido."
            ) from exc
        if not isinstance(decoded, dict):
            raise PersistenceVerificationError(
                f"{method} {path} no devolvió un objeto JSON."
            )
        return status, cast(Mapping[str, object], decoded)

    def csrf(self) -> str:
        _, payload = self.request(
            "GET",
            "/auth/csrf",
            expected={200},
        )
        token = payload.get("csrf_token")
        if not isinstance(token, str) or not token:
            raise PersistenceVerificationError(
                "La API no entregó el token CSRF."
            )
        return token


def _run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PersistenceVerificationError(
            f"Falló {' '.join(command)}: {detail}"
        )
    return result.stdout.strip()


def _psql(statement: str) -> str:
    database = os.environ.get(
        "POSTGRES_DB",
        "continuous_authentication",
    )
    user = os.environ.get("POSTGRES_USER", "continuous_auth_user")
    return _run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            user,
            "-d",
            database,
            "-Atc",
            statement,
        ]
    )


def _wait_for_json(url: str, timeout_seconds: int) -> object:
    deadline = time.monotonic() + timeout_seconds
    last_error = "sin respuesta"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                last_error = f"HTTP {response.status}"
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            urllib.error.URLError,
        ) as exc:
            last_error = str(exc)
        time.sleep(2)
    raise PersistenceVerificationError(
        f"{url} no estuvo disponible: {last_error}"
    )


def _restart_backend(health_url: str) -> object:
    _run(["docker", "compose", "restart", "backend"])
    return _wait_for_json(health_url, 120)


def _cleanup_user(email: str) -> None:
    if not email.startswith(
        "integration-test-persistence-"
    ) or not email.endswith("@example.com"):
        raise PersistenceVerificationError(
            "La limpieza rechazó un correo fuera del prefijo autorizado."
        )
    _psql(
        "DELETE FROM audit_logs WHERE user_id IN "
        f"(SELECT id FROM users WHERE email = '{email}'); "
        f"DELETE FROM users WHERE email = '{email}';"
    )


def _verify_session_and_capture_persistence(
    *,
    health_url: str,
) -> dict[str, object]:
    identifier = uuid4().hex
    email = (
        f"integration-test-persistence-{identifier}@example.com"
    )
    password = f"Persistence-{identifier}-Aa9!"
    api_url = os.environ.get(
        "BACKEND_API_URL",
        "http://localhost:8000/api",
    )
    origin = os.environ.get(
        "FRONTEND_URL",
        "http://localhost:8080",
    )
    session = ApiSession(api_url, origin)
    relative_probe = (
        f"integration-test-persistence/{identifier}.probe"
    )
    container_probe = f"/app/data/captures/{relative_probe}"
    host_probe = PROJECT_ROOT / "data" / "captures" / relative_probe
    registered = False
    try:
        registration = {
            "full_name": f"integration-test-persistence-{identifier}",
            "email": email,
            "password": password,
            "password_confirmation": password,
            "accept_terms": True,
        }
        session.request(
            "POST",
            "/auth/register",
            payload=registration,
            headers={"X-CSRF-Token": session.csrf()},
            expected={201},
        )
        registered = True
        session.request(
            "POST",
            "/auth/login",
            payload={
                "email": email,
                "password": password,
                "remember_me": True,
            },
            headers={"X-CSRF-Token": session.csrf()},
            expected={200},
        )
        session.request("GET", "/auth/me", expected={200})
        active_before = _psql(
            "SELECT COUNT(*) FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            f"WHERE u.email = '{email}' AND s.revoked_at IS NULL;"
        )
        if active_before != "1":
            raise PersistenceVerificationError(
                "No se encontró exactamente una sesión activa antes del reinicio."
            )

        probe_script = (
            "from pathlib import Path; "
            f"p=Path('{container_probe}'); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text('{identifier}', encoding='utf-8')"
        )
        _run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "python",
                "-c",
                probe_script,
            ]
        )
        first_health = _restart_backend(health_url)
        session.request("GET", "/auth/me", expected={200})
        persisted_probe = _run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "python",
                "-c",
                (
                    "from pathlib import Path; "
                    f"print(Path('{container_probe}').read_text("
                    "encoding='utf-8'))"
                ),
            ]
        )
        if persisted_probe != identifier:
            raise PersistenceVerificationError(
                "La captura de prueba no sobrevivió al reinicio."
            )

        session.request(
            "POST",
            "/auth/logout",
            headers={"X-CSRF-Token": session.csrf()},
            expected={200},
        )
        session.request("GET", "/auth/me", expected={401})
        revoked_before_restart = _psql(
            "SELECT COUNT(*) FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            f"WHERE u.email = '{email}' AND s.revoked_at IS NOT NULL;"
        )
        if revoked_before_restart != "1":
            raise PersistenceVerificationError(
                "La revocación no quedó registrada en PostgreSQL."
            )
        second_health = _restart_backend(health_url)
        session.request("GET", "/auth/me", expected={401})
        return {
            "valid_session_survived_restart": True,
            "revoked_session_remained_revoked": True,
            "capture_volume_survived_restart": True,
            "first_restart_health": first_health,
            "second_restart_health": second_health,
        }
    finally:
        host_probe.unlink(missing_ok=True)
        if (
            host_probe.parent.is_dir()
            and not any(host_probe.parent.iterdir())
        ):
            host_probe.parent.rmdir()
        if registered:
            _cleanup_user(email)


def verify() -> dict[str, object]:
    probe_id = str(uuid4())
    resource_id = f"integration-test-persistence-{probe_id}"
    health_url = os.environ.get(
        "BACKEND_HEALTH_URL",
        "http://localhost:8000/api/health",
    )
    inserted = False
    try:
        _psql(
            "INSERT INTO audit_logs "
            "(id, event_type, resource_type, resource_id, created_at) "
            f"VALUES ('{probe_id}'::uuid, 'INTEGRATION_TEST_PERSISTENCE', "
            f"'integration-test', '{resource_id}', NOW());"
        )
        inserted = True
        before = _psql(
            "SELECT COUNT(*) FROM audit_logs "
            f"WHERE resource_id = '{resource_id}';"
        )
        if before != "1":
            raise PersistenceVerificationError(
                "No se confirmó el probe antes del reinicio."
            )
        health = _restart_backend(health_url)
        after = _psql(
            "SELECT COUNT(*) FROM audit_logs "
            f"WHERE resource_id = '{resource_id}';"
        )
        if after != "1":
            raise PersistenceVerificationError(
                "PostgreSQL no conservó el probe después del reinicio."
            )
        model_status: object
        try:
            validation_output = _run(
                [
                    "docker",
                    "compose",
                    "exec",
                    "-T",
                    "backend",
                    "python",
                    "scripts/validate_model_artifacts.py",
                ]
            )
            model_status = {
                "status": "passed",
                "validation_output": validation_output,
            }
        except PersistenceVerificationError as exc:
            model_status = {"status": "blocked", "reason": str(exc)}
        session_and_capture = _verify_session_and_capture_persistence(
            health_url=health_url,
        )
        return {
            "status": "passed",
            "probe": "integration-test-persistence-*",
            "postgres_persisted": True,
            "backend_health": health,
            "session_and_capture": session_and_capture,
            "model_status_after_restart": model_status,
        }
    finally:
        if inserted:
            _psql(
                "DELETE FROM audit_logs "
                f"WHERE resource_id = '{resource_id}';"
            )


def main() -> None:
    print(json.dumps(verify(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
