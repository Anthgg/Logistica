from datetime import datetime

from fastapi.testclient import TestClient

from app.api.routes import health as health_route
from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_health_returns_connected_response(monkeypatch) -> None:
    monkeypatch.setattr(health_route, "is_database_connected", lambda: True)
    response = client.get(f"{settings.API_PREFIX}/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "connected"
    assert payload["service"] == settings.APP_NAME
    assert payload["version"] == settings.APP_VERSION
    assert datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")).tzinfo
    assert response.headers["X-Request-ID"]


def test_health_returns_degraded_without_database(monkeypatch) -> None:
    monkeypatch.setattr(health_route, "is_database_connected", lambda: False)
    response = client.get(f"{settings.API_PREFIX}/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"]["status"] == "disconnected"
    assert settings.DATABASE_URL not in response.text


def test_unknown_route_uses_uniform_error() -> None:
    response = client.get(f"{settings.API_PREFIX}/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_method_not_allowed_uses_uniform_error() -> None:
    response = client.post(f"{settings.API_PREFIX}/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_docs_are_available() -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
