"""Phase 004 — tests for organization, branch and warehouse logistics endpoints."""

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


# ---------------------------------------------------------------------------
# Endpoints are registered
# ---------------------------------------------------------------------------

def test_org_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/organizations" in paths
    assert "/api/logistics/organizations/{organization_id}" in paths
    assert "/api/logistics/organizations/{organization_id}/branches" in paths
    assert "/api/logistics/branches/{branch_id}" in paths
    assert "/api/logistics/branches/{branch_id}/warehouses" in paths
    assert "/api/logistics/warehouses/{warehouse_id}" in paths
    assert "/api/logistics/warehouses/{warehouse_id}/set-default" in paths


# ---------------------------------------------------------------------------
# Auth is required for all endpoints
# ---------------------------------------------------------------------------

def test_org_list_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/organizations")
    assert response.status_code == 401


def test_org_create_requires_auth(client: TestClient) -> None:
    response = client.post("/api/logistics/organizations", json={"code": "T1", "name": "Test", "country_code": "PE"})
    assert response.status_code == 401


def test_branch_list_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/organizations/00000000-0000-0000-0000-000000000001/branches")
    assert response.status_code == 401


def test_warehouse_list_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/branches/00000000-0000-0000-0000-000000000001/warehouses")
    assert response.status_code == 401


def test_warehouse_set_default_requires_auth(client: TestClient) -> None:
    response = client.post("/api/logistics/warehouses/00000000-0000-0000-0000-000000000001/set-default", json={"is_default": True})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Error format is compatible
# ---------------------------------------------------------------------------

def test_org_error_format(client: TestClient) -> None:
    response = client.get("/api/logistics/organizations")
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]


# ---------------------------------------------------------------------------
# Existing routes still work
# ---------------------------------------------------------------------------

def test_existing_health_still_works(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_existing_auth_login_still_works(client: TestClient) -> None:
    # The login endpoint should still be present (may return 422 without body)
    response = client.post("/api/auth/login", json={})
    assert response.status_code in (403, 422, 400)


# ---------------------------------------------------------------------------
# Phase 003 tests still pass
# ---------------------------------------------------------------------------

def test_logistics_health_still_requires_auth(client: TestClient) -> None:
    response = client.get("/api/logistics/health")
    assert response.status_code == 401


def test_phase003_status_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/documents/" in paths
    assert "/api/logistics/routes/" in paths
    assert "/api/logistics/files/" in paths
    assert "/api/logistics/audit-events" in paths
    assert "/api/logistics/integrations/" in paths


# ---------------------------------------------------------------------------
# No new auth endpoints in logistics
# ---------------------------------------------------------------------------

def test_no_logistics_login(client: TestClient) -> None:
    response = client.post("/api/logistics/login", json={})
    # Should be 404 (endpoint doesn't exist)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# OpenAPI generates
# ---------------------------------------------------------------------------

def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 75