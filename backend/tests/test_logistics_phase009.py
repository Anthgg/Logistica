"""Phase 009 — tests for step-up authentication and sensitive operations."""

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
def test_security_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/security/policies" in paths
    assert "/api/logistics/security/step-up/challenges" in paths
    assert "/api/logistics/security/step-up/challenges/{challenge_id}" in paths
    assert "/api/logistics/security/step-up/challenges/{challenge_id}/factors" in paths
    assert "/api/logistics/security/step-up/challenges/{challenge_id}/complete" in paths


# --- Auth required ---
def test_policies_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/security/policies").status_code == 401


def test_create_challenge_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/security/step-up/challenges", json={
        "permission_code": "logistics.documents.cancel",
    }).status_code == 401


def test_get_challenge_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/security/step-up/challenges/00000000-0000-0000-0000-000000000001").status_code == 401


def test_submit_factor_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/security/step-up/challenges/00000000-0000-0000-0000-000000000001/factors", json={
        "factor": "face", "result": "passed",
    }).status_code == 401


def test_complete_challenge_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/security/step-up/challenges/00000000-0000-0000-0000-000000000001/complete", json={}).status_code == 401


# --- Policy catalog ---
def test_policy_version_defined() -> None:
    from app.modules.logistics.security.step_up_policy import POLICY_VERSION
    assert POLICY_VERSION == "1.1.0"


def test_sensitive_permissions_defined() -> None:
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG
    assert len(POLICY_CATALOG) >= 18
    assert "logistics.role_assignments.create" in POLICY_CATALOG
    assert "logistics.documents.cancel" in POLICY_CATALOG
    assert "logistics.quarantine.release" in POLICY_CATALOG


def test_every_step_up_permission_has_a_policy() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

    required = {
        permission["code"]
        for permission in PERMISSIONS
        if permission.get("requires_step_up", False)
    }
    assert required <= set(POLICY_CATALOG)


def test_is_sensitive_permission() -> None:
    from app.modules.logistics.security.step_up_policy import is_sensitive_permission
    assert is_sensitive_permission("logistics.documents.cancel") is True
    assert is_sensitive_permission("logistics.warehouses.read") is False


def test_policy_entry_has_factors() -> None:
    from app.modules.logistics.security.step_up_policy import get_policy
    policy = get_policy("logistics.role_assignments.create")
    assert policy is not None
    assert len(policy.required_factors) >= 1
    assert policy.fail_closed is True
    assert policy.one_time_proof is True


# --- Models import ---
def test_stepup_models_import() -> None:
    import importlib
    for mod in [
        "app.modules.logistics.security.models_stepup",
        "app.modules.logistics.security.step_up_policy",
        "app.modules.logistics.security.step_up_schemas",
        "app.modules.logistics.security.step_up_service",
        "app.modules.logistics.security.step_up_router",
    ]:
        importlib.import_module(mod)


# --- Service ---
def test_step_up_service_exists() -> None:
    from app.modules.logistics.security.step_up_service import step_up_service
    assert step_up_service is not None
    assert hasattr(step_up_service, "create_challenge")
    assert hasattr(step_up_service, "get_challenge")
    assert hasattr(step_up_service, "submit_factor")
    assert hasattr(step_up_service, "complete_challenge")
    assert hasattr(step_up_service, "find_valid_proof")
    assert hasattr(step_up_service, "consume_proof")
    assert hasattr(step_up_service, "revoke_session_proofs")
    assert hasattr(step_up_service, "evaluate_risk")


# --- No DELETE or PATCH endpoints ---
def test_no_stepup_delete(app: FastAPI) -> None:
    schema = app.openapi()
    for path, methods in schema["paths"].items():
        if "step-up" in path:
            for method in methods:
                assert method != "delete", f"DELETE endpoint found at {path}"


# --- No auth duplication ---
def test_no_logistics_login(client: TestClient) -> None:
    assert client.post("/api/logistics/login", json={}).status_code == 404


# --- Regression ---
def test_health_still_works(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 101


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


def test_phase006_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/permissions" in paths
    assert "/api/logistics/me/permissions" in paths


def test_phase007_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/audit-events" in paths


def test_phase008_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/me" in paths
    assert "/api/logistics/me/context" in paths
