"""Phase 008 — tests for logistics authentication integration."""

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


# --- New endpoints registered ---
def test_logistics_me_endpoints_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/me" in paths
    assert "/api/logistics/me/context" in paths


# --- Auth required for /me ---
def test_logistics_me_requires_auth(client: TestClient) -> None:
    assert client.get("/api/logistics/me").status_code == 401


def test_logistics_me_context_requires_auth(client: TestClient) -> None:
    assert client.post("/api/logistics/me/context", json={}).status_code == 401


def test_logistics_me_context_requires_csrf(client: TestClient) -> None:
    # Even with auth, POST without CSRF should fail
    # Without auth, we get 401 first
    assert client.post("/api/logistics/me/context", json={
        "organization_id": "00000000-0000-0000-0000-000000000001",
    }).status_code == 401


# --- No second auth system ---
def test_no_logistics_login(client: TestClient) -> None:
    assert client.post("/api/logistics/login", json={}).status_code == 404


def test_no_logistics_logout(client: TestClient) -> None:
    assert client.post("/api/logistics/logout", json={}).status_code == 404


def test_no_logistics_register(client: TestClient) -> None:
    assert client.post("/api/logistics/register", json={}).status_code == 404


def test_no_logistics_csrf(client: TestClient) -> None:
    assert client.get("/api/logistics/csrf").status_code == 404


# --- Existing auth still works ---
def test_auth_me_still_works(client: TestClient) -> None:
    # Without auth, should return 401 (endpoint exists)
    assert client.get("/api/auth/me").status_code == 401


def test_auth_csrf_still_works(client: TestClient) -> None:
    # CSRF endpoint should be accessible (public)
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200


def test_auth_login_still_exists(client: TestClient) -> None:
    # Login endpoint should exist (may return 422/403 without proper body)
    response = client.post("/api/auth/login", json={})
    assert response.status_code in (403, 422)


# --- Principal model ---
def test_logistics_principal_creation() -> None:
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.modules.logistics.principal import LogisticsPrincipal

    uid = uuid4()
    sid = uuid4()
    p = LogisticsPrincipal(
        user_id=uid, email="test@test.com", full_name="Test",
        platform_role="admin", is_active=True,
        session_id=sid, device_id=None, authentication_level="traditional",
        session_expires_at=datetime.now(timezone.utc),
        risk_score=None, logistics_enabled=True,
    )
    assert p.user_id == uid
    assert p.is_platform_admin is True
    assert p.has_permission("any.permission") is True
    assert p.has_logistics_access is True


def test_logistics_principal_non_admin() -> None:
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.modules.logistics.principal import LogisticsPrincipal

    p = LogisticsPrincipal(
        user_id=uuid4(), email="user@test.com", full_name="User",
        platform_role="user", is_active=True,
        session_id=uuid4(), device_id=None, authentication_level="traditional",
        session_expires_at=datetime.now(timezone.utc),
        risk_score=None, logistics_enabled=True,
        permission_codes=["logistics.warehouses.read"],
    )
    assert p.is_platform_admin is False
    assert p.has_permission("logistics.warehouses.read") is True
    assert p.has_permission("logistics.warehouses.create") is False
    assert p.has_logistics_access is True


def test_logistics_principal_no_access() -> None:
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.modules.logistics.principal import LogisticsPrincipal

    p = LogisticsPrincipal(
        user_id=uuid4(), email="noreply@test.com", full_name="NoAccess",
        platform_role="user", is_active=True,
        session_id=uuid4(), device_id=None, authentication_level="traditional",
        session_expires_at=datetime.now(timezone.utc),
        risk_score=None, logistics_enabled=False,
    )
    assert p.has_logistics_access is False
    assert p.has_permission("any.permission") is False


# --- Access resolver ---
def test_access_resolver_exists() -> None:
    from app.modules.logistics.access_resolver import access_resolver
    assert access_resolver is not None
    assert hasattr(access_resolver, "resolve")


def test_permission_resolution_bulk_loads_metadata_and_roles() -> None:
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.logistics.rbac.permission_service import PermissionService

    user_id = uuid4()
    role_id = uuid4()
    assignment = SimpleNamespace(
        role_id=role_id,
        scope_type="global",
        organization_id=None,
        branch_id=None,
        warehouse_id=None,
        ends_at=None,
    )
    calls = {"permissions": 0, "roles": 0}

    class PermissionRepo:
        def list_by_codes(self, _db, codes):
            calls["permissions"] += 1
            assert set(codes) == {"logistics.inventory_ledger.read", "logistics.audit.read"}
            return [
                SimpleNamespace(
                    code="logistics.inventory_ledger.read",
                    is_sensitive=False,
                    requires_step_up=False,
                ),
                SimpleNamespace(
                    code="logistics.audit.read",
                    is_sensitive=True,
                    requires_step_up=True,
                ),
            ]

        def get_by_code(self, *_args, **_kwargs):
            raise AssertionError("permission metadata must be loaded in bulk")

    class RolePermissionRepo:
        def list_permission_codes_by_roles(self, _db, role_ids):
            assert role_ids == [role_id]
            return ["logistics.inventory_ledger.read", "logistics.audit.read"]

    class RoleRepo:
        def list_by_ids(self, _db, role_ids):
            calls["roles"] += 1
            assert role_ids == [role_id]
            return [
                SimpleNamespace(
                    id=role_id,
                    code="LOGISTICS_ADMIN",
                    name="Administrador logístico",
                )
            ]

        def get_by_id(self, *_args, **_kwargs):
            raise AssertionError("role metadata must be loaded in bulk")

    service = PermissionService()
    service.perm_repo = PermissionRepo()
    service.role_perm_repo = RolePermissionRepo()
    service.role_repo = RoleRepo()
    service.assignment_repo = SimpleNamespace(
        list_active_by_user=lambda *_args: (_ for _ in ()).throw(
            AssertionError("provided assignments must be reused")
        )
    )

    result = service.resolve_effective_permissions(
        None,
        user_id,
        assignments=[assignment],
    )

    assert calls == {"permissions": 1, "roles": 1}
    assert result.permissions == [
        "logistics.audit.read",
        "logistics.inventory_ledger.read",
    ]
    assert result.sensitive_permissions == ["logistics.audit.read"]
    assert result.step_up_permissions == ["logistics.audit.read"]
    assert result.roles[0]["role_code"] == "LOGISTICS_ADMIN"


def test_access_resolver_queries_assignments_once(monkeypatch) -> None:
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.logistics import access_resolver as resolver_module

    user_id = uuid4()
    role_id = uuid4()
    assignments = [
        SimpleNamespace(
            role_id=role_id,
            organization_id=None,
            branch_id=None,
            warehouse_id=None,
        )
    ]
    assignment_calls = 0

    class AssignmentRepo:
        def list_active_by_user(self, _db, requested_user_id):
            nonlocal assignment_calls
            assignment_calls += 1
            assert requested_user_id == user_id
            return assignments

    class PermissionServiceStub:
        def resolve_effective_permissions(
            self,
            _db,
            requested_user_id,
            *,
            assignments: list,
        ):
            assert requested_user_id == user_id
            assert assignments is assignments_for_assertion
            return SimpleNamespace(
                permissions=["logistics.inventory_ledger.read"],
                sensitive_permissions=[],
                step_up_permissions=[],
                roles=[{"role_code": "LOGISTICS_ADMIN"}],
            )

    assignments_for_assertion = assignments
    monkeypatch.setattr(resolver_module, "_assignment_repo", AssignmentRepo())
    monkeypatch.setattr(
        resolver_module,
        "_permission_service",
        PermissionServiceStub(),
    )

    principal = resolver_module.LogisticsAccessResolver().resolve(
        None,
        SimpleNamespace(
            id=user_id,
            email="test@example.com",
            full_name="Test",
            role="admin",
            is_active=True,
        ),
        SimpleNamespace(
            id=uuid4(),
            device_id=None,
            authentication_level="traditional",
            expires_at=datetime.now(timezone.utc),
            risk_score=None,
        ),
    )

    assert assignment_calls == 1
    assert principal.permission_codes == ["logistics.inventory_ledger.read"]


# --- Auth dependencies ---
def test_get_logistics_principal_is_callable() -> None:
    from app.modules.logistics.auth_dependencies import get_logistics_principal
    assert callable(get_logistics_principal)


def test_require_logistics_access_is_callable() -> None:
    from app.modules.logistics.auth_dependencies import require_logistics_access
    assert callable(require_logistics_access)


# --- Models import ---
def test_phase008_models_import() -> None:
    import importlib
    for mod in [
        "app.modules.logistics.principal",
        "app.modules.logistics.access_resolver",
        "app.modules.logistics.auth_dependencies",
        "app.modules.logistics.me_schemas",
        "app.modules.logistics.me_router",
    ]:
        importlib.import_module(mod)


# --- Regression ---
def test_health_still_works(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_openapi_still_generates(app: FastAPI) -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert len(schema["paths"]) >= 96


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


def test_phase007_endpoints_still_registered(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/audit-events" in paths


# --- No duplicate auth endpoints ---
def test_no_duplicate_auth_in_logistics(app: FastAPI) -> None:
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    # These auth endpoints should NOT exist under /api/logistics
    assert "/api/logistics/auth/login" not in paths
    assert "/api/logistics/auth/logout" not in paths
    assert "/api/logistics/auth/me" not in paths
    assert "/api/logistics/auth/csrf" not in paths
    assert "/api/logistics/auth/register" not in paths


# --- Error format ---
def test_logistics_me_error_format(client: TestClient) -> None:
    response = client.get("/api/logistics/me")
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
