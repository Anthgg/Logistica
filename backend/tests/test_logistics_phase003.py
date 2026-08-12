"""Phase 003 — integration tests for the logistics modular architecture."""

import importlib
import inspect
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _collect_paths(app: FastAPI) -> set[str]:
    """Collect all route paths from the OpenAPI schema."""
    try:
        schema = app.openapi()
        return set(schema.get("paths", {}).keys())
    except Exception:
        return set()


@pytest.fixture(scope="module")
def app() -> FastAPI:
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# 1. Application starts
def test_application_starts(app: FastAPI) -> None:
    assert app is not None
    assert callable(app)


# 2. Existing routers still registered
def test_existing_routes_present(app: FastAPI) -> None:
    routes = _collect_paths(app)
    assert "/api/health" in routes
    assert "/api/auth/login" in routes
    assert "/api/auth/me" in routes
    assert "/api/auth/sessions" in routes


# 3. Logistics router registered
def test_logistics_router_registered(app: FastAPI) -> None:
    routes = _collect_paths(app)
    assert "/api/logistics/health" in routes
    assert "/api/logistics/documents/" in routes
    assert "/api/logistics/routes/" in routes
    assert "/api/logistics/files/" in routes
    # Phase 007 replaced audit/ status endpoint with audit-events
    assert "/api/logistics/integrations/" in routes


# 4. No duplicate prefix
def test_no_duplicate_prefix(app: FastAPI) -> None:
    routes = _collect_paths(app)
    assert not any(r.startswith("/api/api/logistics") for r in routes)


# 5. OpenAPI generates
def test_openapi_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert "/api/logistics/health" in schema["paths"]


# 6. Modules import without circular deps
def test_no_circular_imports() -> None:
    modules_to_check = [
        "app.modules.logistics",
        "app.modules.logistics.router",
        "app.modules.logistics.constants",
        "app.modules.logistics.exceptions",
        "app.modules.logistics.dependencies",
        "app.modules.logistics.documents.domain.contracts",
        "app.modules.logistics.documents.application.services",
        "app.modules.logistics.documents.api.router",
        "app.modules.logistics.routes_module.domain.contracts",
        "app.modules.logistics.routes_module.api.router",
        "app.modules.logistics.files.domain.contracts",
        "app.modules.logistics.files.api.router",
        "app.modules.logistics.audit.domain.contracts",
        "app.modules.logistics.audit.api.router",
        "app.modules.logistics.integrations.domain.contracts",
        "app.modules.logistics.integrations.api.router",
    ]
    for mod_name in modules_to_check:
        importlib.import_module(mod_name)


# 7. Domain contracts don't depend on FastAPI
def test_domain_contracts_no_fastapi() -> None:
    domain_modules = [
        "app.modules.logistics.documents.domain.contracts",
        "app.modules.logistics.routes_module.domain.contracts",
        "app.modules.logistics.files.domain.contracts",
        "app.modules.logistics.audit.domain.contracts",
        "app.modules.logistics.integrations.domain.contracts",
    ]
    for mod_name in domain_modules:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        assert "from fastapi" not in source, f"{mod_name} imports FastAPI"
        assert "import fastapi" not in source, f"{mod_name} imports FastAPI"


# 8. Domain contracts don't depend on external SDKs
def test_domain_contracts_no_external_sdk() -> None:
    forbidden = ["google.cloud", "boto3", "requests", "httpx", "openrouteservice", "mapbox", "osrm"]
    domain_modules = [
        "app.modules.logistics.documents.domain.contracts",
        "app.modules.logistics.routes_module.domain.contracts",
        "app.modules.logistics.files.domain.contracts",
        "app.modules.logistics.audit.domain.contracts",
        "app.modules.logistics.integrations.domain.contracts",
    ]
    for mod_name in domain_modules:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        for f in forbidden:
            assert f not in source, f"{mod_name} imports {f}"


# 9. Authentication not duplicated
def test_auth_not_duplicated() -> None:
    from app.modules.logistics import create_logistics_router
    router = create_logistics_router()
    paths = _collect_paths_from_router(router)
    assert "/login" not in paths
    assert "/logout" not in paths
    assert "/register" not in paths
    assert "/me" not in paths
    assert "/refresh" not in paths
    assert "/csrf" not in paths


def _collect_paths_from_router(router) -> set[str]:
    paths: set[str] = set()
    for route in router.routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        elif hasattr(route, "routes"):
            for sub in route.routes:
                if hasattr(sub, "path"):
                    paths.add(sub.path)
    return paths


# 10. No new migrations
def test_no_new_migrations() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    versions_dir = backend_dir / "alembic" / "versions"
    if versions_dir.exists():
        for mf in versions_dir.glob("*.py"):
            content = mf.read_text(encoding="utf-8", errors="ignore")
            assert "logistics_documents" not in content
            assert "logistics_files" not in content
            


# 11. Health endpoint requires auth
def test_logistics_health_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/health")
    assert response.status_code == 401


# 12. Error format compatible
def test_error_format_compatible(client: TestClient) -> None:
    response = client.get("/api/logistics/health")
    data = response.json()
    assert "success" in data
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


# 13. Permission convention
def test_permission_convention() -> None:
    from app.modules.logistics.constants import LogisticsPermission
    for perm in LogisticsPermission:
        parts = perm.value.split(".")
        assert len(parts) == 3
        assert parts[0] == "logistics"
