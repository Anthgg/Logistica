"""Phase 006 — tests for logistics permissions, authorization and catalog."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def app() -> FastAPI:
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# --- Endpoints registered ---
def test_permission_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/permissions" in paths
    assert "/api/logistics/permissions/{permission_id}" in paths
    assert "/api/logistics/me/permissions" in paths
    assert "/api/logistics/authorization/check" in paths
    assert "/api/logistics/roles/{role_id}/permissions" in paths


# --- Auth required ---
def test_permissions_list_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/permissions").status_code == 401


def test_my_permissions_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/me/permissions").status_code == 401


def test_auth_check_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/authorization/check", json={
        "permission_code": "logistics.warehouses.read"
    }).status_code == 401


# --- Catalog constants ---
def test_catalog_version_defined() -> None:
    from app.modules.logistics.rbac.permission_catalog import CATALOG_VERSION
    assert CATALOG_VERSION == "1.1.0"


def test_permissions_defined() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    assert len(PERMISSIONS) >= 100  # We have ~110+ permissions


def test_role_permission_matrix_defined() -> None:
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX
    assert len(ROLE_PERMISSION_MATRIX) == 16  # All 16 roles
    assert "LOGISTICS_ADMIN" in ROLE_PERMISSION_MATRIX
    assert "DRIVER" in ROLE_PERMISSION_MATRIX
    assert len(ROLE_PERMISSION_MATRIX["LOGISTICS_ADMIN"]) > 20


def test_permission_codes_follow_convention() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    for perm in PERMISSIONS:
        code = perm["code"]
        parts = code.split(".")
        assert len(parts) >= 3, f"Permission {code} does not follow logistics.<resource>.<action>"
        assert parts[0] == "logistics", f"Permission {code} does not start with 'logistics'"


def test_sensitive_permissions_exist() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    sensitive = [p for p in PERMISSIONS if p.get("is_sensitive")]
    assert len(sensitive) >= 15


def test_step_up_permissions_exist() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    step_up = [p for p in PERMISSIONS if p.get("requires_step_up")]
    assert len(step_up) >= 10


def test_requires_reason_permissions_exist() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    reason = [p for p in PERMISSIONS if p.get("requires_reason")]
    assert len(reason) >= 15


# --- Models import ---
def test_permission_models_import() -> None:
    import importlib
    for mod in [
        "app.modules.logistics.rbac.models_permission",
        "app.modules.logistics.rbac.models_role_permission",
        "app.modules.logistics.rbac.models_permission_scope",
        "app.modules.logistics.rbac.permission_catalog",
        "app.modules.logistics.rbac.permission_schemas",
        "app.modules.logistics.rbac.permission_repository",
        "app.modules.logistics.rbac.permission_service",
        "app.modules.logistics.rbac.authorization",
    ]:
        importlib.import_module(mod)


# --- Authorization dependency ---
def test_require_logistics_permission_returns_callable() -> None:
    from app.modules.logistics.rbac.authorization import require_logistics_permission
    dep = require_logistics_permission("logistics.warehouses.read")
    assert callable(dep)


# --- Regression ---
def test_health_still_works(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 90


def test_phase003_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/documents" in paths
    assert "/api/logistics/health" in paths


def test_phase004_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/organizations" in paths


def test_phase005_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/roles" in paths
    assert "/api/logistics/me/roles" in paths


def test_no_logistics_login(client: TestClient) -> None:
    assert client.post("/api/logistics/login", json={}).status_code == 404
