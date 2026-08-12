"""Phase 005 — tests for logistics RBAC: roles, assignments, effective roles."""

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
def test_rbac_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/roles" in paths
    assert "/api/logistics/roles/{role_id}" in paths
    assert "/api/logistics/roles/{role_id}/scope-rules" in paths
    assert "/api/logistics/me/roles" in paths
    assert "/api/logistics/role-assignments" in paths
    assert "/api/logistics/role-assignments/{assignment_id}" in paths
    assert "/api/logistics/role-assignments/{assignment_id}/revoke" in paths
    assert "/api/logistics/role-assignments/{assignment_id}/dates" in paths
    assert "/api/logistics/role-assignments/validate-conflicts" in paths
    assert "/api/logistics/users/{user_id}/role-assignments" in paths


# --- Auth required ---
def test_roles_list_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/roles")
    assert response.status_code == 401


def test_me_roles_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/me/roles")
    assert response.status_code == 401


def test_create_assignment_requires_auth(client: TestClient) -> None:
    response = client.post("/api/logistics/role-assignments", json={
        "user_id": "00000000-0000-0000-0000-000000000001",
        "role_id": "00000000-0000-0000-0000-000000000002",
        "scope_type": "global",
    })
    assert response.status_code == 401


def test_revoke_assignment_requires_auth(client: TestClient) -> None:
    response = client.post("/api/logistics/role-assignments/00000000-0000-0000-0000-000000000001/revoke",
                           json={"revocation_reason": "test"})
    assert response.status_code == 401


def test_validate_conflicts_requires_auth(client: TestClient) -> None:
    response = client.post("/api/logistics/role-assignments/validate-conflicts"
                           "?role_a_id=00000000-0000-0000-0000-000000000001"
                           "&role_b_id=00000000-0000-0000-0000-000000000002")
    assert response.status_code == 401


# --- No auth duplication ---
def test_no_logistics_login_endpoint(client: TestClient) -> None:
    response = client.post("/api/logistics/login", json={})
    assert response.status_code == 404


# --- Error format ---
def test_rbac_error_format(client: TestClient) -> None:
    response = client.get("/api/logistics/roles")
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]


# --- Regression: existing endpoints still work ---
def test_health_still_works(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_phase003_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/documents/" in paths
    assert "/api/logistics/routes/" in paths


def test_phase004_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/organizations" in paths
    assert "/api/logistics/warehouses/{warehouse_id}" in paths


def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 80


# --- Catalog constants ---
def test_system_roles_defined() -> None:
    from app.modules.logistics.rbac.catalog import SYSTEM_ROLES
    assert len(SYSTEM_ROLES) == 16
    codes = [r["code"] for r in SYSTEM_ROLES]
    assert "LOGISTICS_ADMIN" in codes
    assert "DRIVER" in codes
    assert "WAREHOUSE_OPERATOR" in codes
    assert "LOGISTICS_VIEWER" in codes


def test_scope_types_defined() -> None:
    from app.modules.logistics.rbac.catalog import ScopeType
    assert ScopeType.GLOBAL == "global"
    assert ScopeType.ORGANIZATION == "organization"
    assert ScopeType.BRANCH == "branch"
    assert ScopeType.WAREHOUSE == "warehouse"


def test_conflict_rules_defined() -> None:
    from app.modules.logistics.rbac.catalog import CONFLICT_RULES
    assert len(CONFLICT_RULES) >= 4
    types = [r["conflict_type"] for r in CONFLICT_RULES]
    assert "prohibited" in types
    assert "requires_review" in types


# --- Models import without circular deps ---
def test_rbac_models_import() -> None:
    import importlib
    for mod in [
        "app.modules.logistics.rbac.models_role",
        "app.modules.logistics.rbac.models_scope_rule",
        "app.modules.logistics.rbac.models_assignment",
        "app.modules.logistics.rbac.models_conflict",
        "app.modules.logistics.rbac.catalog",
        "app.modules.logistics.rbac.schemas",
        "app.modules.logistics.rbac.repository",
        "app.modules.logistics.rbac.service",
        "app.modules.logistics.rbac.api.router",
    ]:
        importlib.import_module(mod)
