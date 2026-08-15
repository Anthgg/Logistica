"""Phase 007 — tests for unified audit events."""

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
def test_audit_event_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/audit-events" in paths
    assert "/api/logistics/audit-events/{event_id}" in paths
    assert "/api/logistics/audit-events/by-resource/{resource_type}/{resource_id}" in paths
    assert "/api/logistics/audit-events/by-correlation/{correlation_id}" in paths
    assert "/api/logistics/audit-events/{event_id}/verify-integrity" in paths


# --- No DELETE or PATCH endpoints ---
def test_no_audit_delete_endpoint(app: FastAPI) -> None:
    schema = app.openapi()
    for path, methods in schema["paths"].items():
        if "audit-events" in path:
            for method in methods:
                assert method != "delete", f"DELETE endpoint found at {path}"
                assert method != "patch", f"PATCH endpoint found at {path}"


# --- Auth required ---
def test_audit_list_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/audit-events").status_code == 401


def test_audit_detail_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/audit-events/00000000-0000-0000-0000-000000000001").status_code == 401


def test_audit_integrity_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/audit-events/00000000-0000-0000-0000-000000000001/verify-integrity").status_code == 401


# --- Catalog ---
def test_event_catalog_defined() -> None:
    from app.modules.logistics.audit.catalog import EVENT_CATALOG, CATALOG_VERSION
    assert CATALOG_VERSION == "1.0.0"
    assert len(EVENT_CATALOG) >= 25


def test_event_codes_unique() -> None:
    from app.modules.logistics.audit.catalog import EVENT_CATALOG
    codes = [e["event_code"] for e in EVENT_CATALOG]
    assert len(codes) == len(set(codes)), "Duplicate event codes found"


def test_event_codes_follow_convention() -> None:
    from app.modules.logistics.audit.catalog import EVENT_CATALOG
    for e in EVENT_CATALOG:
        code = e["event_code"]
        assert code.startswith("logistics."), f"Event code {code} doesn't start with 'logistics.'"


def test_is_valid_event_code() -> None:
    from app.modules.logistics.audit.catalog import is_valid_event_code
    assert is_valid_event_code("logistics.organization.created")
    assert not is_valid_event_code("invalid.code")


# --- Sanitizer ---
def test_sanitizer_redacts_sensitive_fields() -> None:
    from app.modules.logistics.audit.sanitizer import sanitize_for_audit
    data = {"name": "test", "password": "secret123", "token": "abc", "email": "user@test.com"}
    result = sanitize_for_audit(data)
    assert result["password"] == "[REDACTED]"
    assert result["token"] == "[REDACTED]"
    assert result["name"] == "test"
    assert result["email"] == "user@test.com"


def test_sanitizer_handles_nested() -> None:
    from app.modules.logistics.audit.sanitizer import sanitize_for_audit
    data = {"outer": {"password": "secret", "name": "test"}}
    result = sanitize_for_audit(data)
    assert result["outer"]["password"] == "[REDACTED]"
    assert result["outer"]["name"] == "test"


def test_sanitizer_handles_none() -> None:
    from app.modules.logistics.audit.sanitizer import sanitize_for_audit
    assert sanitize_for_audit(None) is None


def test_compute_changed_fields() -> None:
    from app.modules.logistics.audit.sanitizer import compute_changed_fields
    assert compute_changed_fields(None, None) == []
    assert compute_changed_fields(None, {"a": 1}) == ["a"]
    assert compute_changed_fields({"a": 1}, {"a": 1}) == []
    assert sorted(compute_changed_fields({"a": 1}, {"a": 2})) == ["a"]
    assert sorted(compute_changed_fields({"a": 1}, {"a": 2, "b": 3})) == ["a", "b"]


# --- Models import ---
def test_audit_models_import() -> None:
    import importlib
    for mod in [
        "app.modules.logistics.audit.models_event",
        "app.modules.logistics.audit.catalog",
        "app.modules.logistics.audit.sanitizer",
        "app.modules.logistics.audit.schemas",
        "app.modules.logistics.audit.service",
        "app.modules.logistics.audit.api.router",
    ]:
        importlib.import_module(mod)


# --- Service ---
def test_audit_service_singleton() -> None:
    from app.modules.logistics.audit.service import audit_service
    assert audit_service is not None
    assert hasattr(audit_service, "write_event")
    assert hasattr(audit_service, "get_by_id")
    assert hasattr(audit_service, "list")
    assert hasattr(audit_service, "verify_integrity")
    assert not hasattr(audit_service, "update")
    assert not hasattr(audit_service, "delete")


# --- Regression ---
def test_health_still_works(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 94


def test_phase003_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/documents/" in paths
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


def test_phase006_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/permissions" in paths
    assert "/api/logistics/me/permissions" in paths


def test_audit_service_list_signature_compatibility() -> None:
    from app.modules.logistics.audit.service import audit_service
    import inspect
    sig = inspect.signature(audit_service.list)
    params = sig.parameters
    assert "category" in params
    assert "event_category" in params
    assert "organization_id" in params
    assert "branch_id" in params
    assert "warehouse_id" in params


def test_audit_events_http_authenticated_success(app: FastAPI) -> None:
    from uuid import uuid4
    from app.dependencies.auth import get_current_user
    from app.models.user import User

    mock_user = User(
        id=uuid4(),
        email="test_audit_admin@example.com",
        full_name="Audit Administrator",
        role="admin",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        client = TestClient(app)
        # 1. Base list query
        response = client.get("/api/logistics/audit-events?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 20

        # 2. Filtered with category query param
        res_cat = client.get("/api/logistics/audit-events?page=1&page_size=20&category=document")
        assert res_cat.status_code == 200
        data_cat = res_cat.json()
        assert "items" in data_cat
        assert "total" in data_cat

        # 3. Filtered with organization_id query param
        dummy_org = str(uuid4())
        res_org = client.get(f"/api/logistics/audit-events?page=1&page_size=20&organization_id={dummy_org}")
        assert res_org.status_code == 200
        data_org = res_org.json()
        assert data_org["items"] == []
        assert data_org["total"] == 0

        # 4. Filtered with branch_id and warehouse_id
        dummy_branch = str(uuid4())
        dummy_wh = str(uuid4())
        res_all = client.get(
            f"/api/logistics/audit-events?page=1&page_size=20&branch_id={dummy_branch}&warehouse_id={dummy_wh}"
        )
        assert res_all.status_code == 200
        data_all = res_all.json()
        assert data_all["items"] == []
        assert data_all["total"] == 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)
