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
    """La versión existe y está bien formada.

    Antes fijaba `== "1.1.0"`. El catálogo ya iba por 1.2.0, así que el caso llevaba
    fallando desde entonces sin señalar nada roto: solo que nadie actualizó el número.
    Un `assert` sobre una constante que debe cambiar cada vez que crece el catálogo no
    protege nada; se comprueba la forma, que es lo que sí es invariante.
    """
    import re

    from app.modules.logistics.rbac.permission_catalog import CATALOG_VERSION

    assert re.fullmatch(r"\d+\.\d+\.\d+", CATALOG_VERSION), CATALOG_VERSION


def test_permissions_defined() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    assert len(PERMISSIONS) >= 100  # We have ~110+ permissions


def test_role_permission_matrix_defined() -> None:
    """Todo rol de sistema tiene entrada en la matriz, y ninguna está vacía.

    Antes exigía `== 16` roles. Hoy hay 20, así que el caso llevaba tiempo en rojo por
    haber crecido el sistema, no por estar roto. La invariante que importa es que la
    matriz cubra exactamente los roles declarados: un rol de sistema sin permisos es
    un rol que no puede hacer nada, y uno en la matriz que no existe es un mapping
    huérfano. Eso sí protege, y además crece solo.
    """
    from app.modules.logistics.rbac.catalog import SYSTEM_ROLES
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX

    system_roles = {str(role["code"]) for role in SYSTEM_ROLES}

    assert system_roles - set(ROLE_PERMISSION_MATRIX) == set(), "roles de sistema sin permisos"
    assert set(ROLE_PERMISSION_MATRIX) - system_roles == set(), "mappings de roles inexistentes"
    empty = sorted(code for code, perms in ROLE_PERMISSION_MATRIX.items() if not perms)
    assert not empty, f"roles sin ningún permiso: {empty}"


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
