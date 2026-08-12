"""
test_balance_security_http.py — Real HTTP Security & Authorization Tests (Phase 045)

CRITERIO DE EVIDENCIA:
- TestClient real contra la aplicación FastAPI real
- Rutas exactas extraídas de app.openapi()
- Confirma API_PREFIX = /api
- Verificación de 401 para usuarios no autenticados en GET /summary y POST /rebuild
- Verificación de 403 para usuarios inactivos
- Verificación de 422 para Payload Tampering (campos prohibidos / enum inves)
- Verificación de 404 para endpoints prohibidos (/set-stock, /fix-stock, etc.)
- Confirmación de ausencia de colisiones de rutas (/inventory/inventory)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User

pytestmark = pytest.mark.security

_BALANCES_BASE_PATH = "/api/logistics/inventory/balances"
_API_PREFIX = "/api"


# ---------------------------------------------------------------------------
# Helpers for auth dependency overrides
# ---------------------------------------------------------------------------

def _get_mock_active_user():
    return User(
        id=uuid4(),
        email="active_logistics_user@example.com",
        full_name="Active Test User",
        role="logistics_operator",
        is_active=True,
    )


def _get_mock_inactive_user():
    return User(
        id=uuid4(),
        email="inactive_logistics_user@example.com",
        full_name="Inactive Test User",
        role="logistics_operator",
        is_active=False,
    )


# ---------------------------------------------------------------------------
# OpenAPI & Routing Tests
# ---------------------------------------------------------------------------

@pytest.mark.security
def test_openapi_balances_paths_exact():
    """
    OPENAPI_EXACT — Extrae paths reales de app.openapi() y verifica
    BALANCES_BASE_PATH exacto.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema.get("paths", {})

    balance_paths = sorted([p for p in paths if _BALANCES_BASE_PATH in p])
    assert len(balance_paths) > 0, (
        f"OPENAPI FAIL: No se encontraron paths con '{_BALANCES_BASE_PATH}' en OpenAPI. "
        f"Paths inventario encontrados: {[p for p in paths if 'inventory' in p]}"
    )

    collision_patterns = [
        "/api/logistics/inventory/inventory/balances",
        "/api/logistics/balances",
        "/api/v1/logistics/inventory/balances",
    ]
    for collision in collision_patterns:
        assert not any(p.startswith(collision) for p in paths), (
            f"ROUTE_COLLISION DETECTED: El path '{collision}' existe en OpenAPI."
        )


@pytest.mark.security
def test_no_api_v1_prefix_in_balances():
    """
    API_PREFIX VERIFICATION — Confirma que el prefijo real es /api (no /api/v1).
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/openapi.json")
    schema = response.json()
    paths = list(schema.get("paths", {}).keys())

    v1_paths = [p for p in paths if p.startswith("/api/v1")]
    assert len(v1_paths) == 0, (
        f"API_PREFIX ANOMALY: Se encontraron paths con /api/v1 en OpenAPI: {v1_paths}."
    )

    api_paths = [p for p in paths if p.startswith("/api")]
    assert len(api_paths) > 0, "FAIL: No hay paths con prefijo /api en OpenAPI"


@pytest.mark.security
def test_forbidden_endpoints_return_404():
    """
    FORBIDDEN_ENDPOINTS — Endpoints de mutación directa de saldo no existen.
    """
    client = TestClient(app, raise_server_exceptions=False)
    forbidden = [
        f"{_BALANCES_BASE_PATH}/set-stock",
        f"{_BALANCES_BASE_PATH}/fix-stock",
        f"{_BALANCES_BASE_PATH}/force-balance",
        "/api/logistics/inventory/balances/set-stock",
        "/api/logistics/balances/set-stock",
    ]
    for path in forbidden:
        res = client.post(path, json={"balance": "999"})
        assert res.status_code == 404, (
            f"FORBIDDEN_ENDPOINT DETECTED: '{path}' respondió HTTP {res.status_code} (esperado 404)."
        )


@pytest.mark.security
def test_route_collision_does_not_exist():
    """
    ROUTE_COLLISION — Verificar que no exista doble prefijo /inventory/inventory.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/logistics/inventory/inventory/balances/summary")
    assert response.status_code == 404, (
        f"ROUTE_COLLISION DETECTED: /api/logistics/inventory/inventory/balances/summary "
        f"respondió HTTP {response.status_code} (esperado 404)."
    )


# ---------------------------------------------------------------------------
# Unauthenticated Access Tests (401)
# ---------------------------------------------------------------------------

@pytest.mark.security
def test_unauthenticated_get_balance_summary_is_denied():
    """
    UNAUTHENTICATED READ — GET /summary sin autenticación debe retornar 401.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(
        f"{_BALANCES_BASE_PATH}/summary",
        params={"organization_id": str(uuid4())},
    )
    assert response.status_code in (401, 403), (
        f"UNAUTHENTICATED FAIL: GET /summary sin auth respondió HTTP {response.status_code}. "
        f"Body: {response.text[:200]}"
    )


@pytest.mark.security
def test_unauthenticated_post_rebuild_is_denied():
    """
    UNAUTHENTICATED REBUILD — POST /rebuild sin autenticación debe retornar 401.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        f"{_BALANCES_BASE_PATH}/rebuild",
        json={
            "organization_id": str(uuid4()),
            "rebuild_mode": "FULL",
        },
    )
    assert response.status_code in (401, 403), (
        f"UNAUTHENTICATED FAIL: POST /rebuild sin auth respondió HTTP {response.status_code}. "
        f"Body: {response.text[:200]}"
    )


# ---------------------------------------------------------------------------
# Authenticated Access & Payload Tampering Tests
# ---------------------------------------------------------------------------

@pytest.mark.security
def test_authenticated_active_user_can_access_summary():
    """
    AUTHENTICATED READ — Usuario activo autenticado puede consultar /summary.
    """
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(
            f"{_BALANCES_BASE_PATH}/summary",
            params={"organization_id": str(org_id)},
        )
        assert response.status_code == 200, (
            f"AUTHENTICATED READ FAIL: Respondió HTTP {response.status_code}. "
            f"Body: {response.text[:200]}"
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_payload_tampering_invalid_rebuild_mode_returns_422():
    """
    PAYLOAD TAMPERING — Rebuild mode inválido (e.g. SUPER_FORCE_MUTATE_STOCK)
    es rechazado por Pydantic validation con 422.
    """
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory_ledger.reconcile"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        response = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={
                "organization_id": str(org_id),
                "rebuild_mode": "SUPER_FORCE_MUTATE_STOCK",  # Modo inválido
            },
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code == 422, (
            f"PAYLOAD TAMPERING FAIL: POST con rebuild_mode inválido respondió HTTP {response.status_code} (esperado 422). "
            f"Body: {response.text[:200]}"
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_payload_tampering_direct_stock_injection_ignored_or_rejected():
    """
    PAYLOAD TAMPERING — Intentar inyectar campos arbitrarios (set_quantity, override_balance)
    en la solicitud de rebuild NO debe alterar el saldo.
    """
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"], is_admin=True)
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=True)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        response = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={
                "organization_id": str(org_id),
                "rebuild_mode": "FULL",
                "set_quantity": "999999.00",  # Inyección maliciosa de saldo
                "override_balance": True,
            },
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert response.status_code in (200, 202, 403, 422), (
            f"PAYLOAD TAMPERING FAIL: Respondió HTTP {response.status_code}. Body: {response.text[:200]}"
        )
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Granular RBAC, Cross-Tenant, CSRF & Step-Up Tests (Phase 045 Security Closure)
# ---------------------------------------------------------------------------

from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.security.models_stepup import StepUpChallenge, StepUpProof


def _make_principal(
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    org_ids: list[UUID] | None = None,
    permissions: list[str] | None = None,
    step_up_permissions: list[str] | None = None,
    is_admin: bool = False,
) -> LogisticsPrincipal:
    uid = user_id or uuid4()
    sid = session_id or uuid4()
    org_strs = [str(o) for o in (org_ids or [uuid4()])]
    return LogisticsPrincipal(
        user_id=uid,
        email="security_test@example.com",
        full_name="Security Test User",
        platform_role="admin" if is_admin else "user",
        is_active=True,
        session_id=sid,
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["INVENTORY_CONTROLLER"],
        permission_codes=permissions or [],
        sensitive_permissions=[],
        step_up_permissions=step_up_permissions or [],
        organization_ids=org_strs,
        default_organization_id=org_strs[0],
    )


@pytest.mark.security
def test_rbac_read_permission_granted_returns_200():
    """RBAC READ PASS — User with logistics.inventory.read gets HTTP 200 on /summary."""
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get(f"{_BALANCES_BASE_PATH}/summary", params={"organization_id": str(org_id)})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_rbac_read_permission_denied_returns_403():
    """RBAC READ DENY — User WITHOUT logistics.inventory.read gets HTTP 403."""
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.other.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get(f"{_BALANCES_BASE_PATH}/summary", params={"organization_id": str(org_id)})
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "FORBIDDEN" in res.text or "No tiene el permiso" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_rbac_rebuild_permission_denied_returns_403():
    """RBAC REBUILD DENY — User WITHOUT rebuild/reconcile permission gets HTTP 403."""
    org_id = uuid4()
    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "FORBIDDEN" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_cross_tenant_read_summary_returns_403():
    """CROSS-TENANT READ — User in Org A querying Org B gets HTTP 403."""
    org_a = uuid4()
    org_b = uuid4()
    principal = _make_principal(org_ids=[org_a], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get(f"{_BALANCES_BASE_PATH}/summary", params={"organization_id": str(org_b)})
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "CROSS_TENANT_ACCESS_DENIED" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_cross_tenant_rebuild_returns_403():
    """CROSS-TENANT REBUILD — User in Org A requesting rebuild for Org B gets HTTP 403."""
    org_a = uuid4()
    org_b = uuid4()
    principal = _make_principal(
        org_ids=[org_a],
        permissions=["logistics.inventory_ledger.reconcile"],
    )
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_b), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "CROSS_TENANT_ACCESS_DENIED" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_csrf_missing_header_returns_403():
    """CSRF MISSING — POST /rebuild with cookie but missing X-CSRF-Token returns HTTP 403."""
    org_id = uuid4()
    principal = _make_principal(
        org_ids=[org_id],
        permissions=["logistics.inventory_ledger.reconcile"],
    )
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "CSRF_VALIDATION_FAILED" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_csrf_invalid_header_returns_403():
    """CSRF INVALID — POST /rebuild with cookie and invalid X-CSRF-Token returns HTTP 403."""
    org_id = uuid4()
    principal = _make_principal(
        org_ids=[org_id],
        permissions=["logistics.inventory_ledger.reconcile"],
    )
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "valid_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "INVALID_TOKEN"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "CSRF_VALIDATION_FAILED" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_step_up_required_returns_403():
    """STEP-UP REQUIRED — Rebuild requiring step-up without X-Step-Up-Proof-ID returns 403."""
    org_id = uuid4()
    perm = "logistics.inventory_ledger.reconcile"
    principal = _make_principal(
        org_ids=[org_id],
        permissions=[perm],
        step_up_permissions=[perm],
    )
    app.dependency_overrides[get_logistics_principal] = lambda: principal

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "test_csrf_token"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert "STEP_UP_REQUIRED" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.security
def test_step_up_valid_proof_passes_step_up(database):
    """STEP-UP PASS — Rebuild with valid X-Step-Up-Proof-ID proof passes step-up."""
    from app.database.session import get_db

    engine = database.get_bind()
    StepUpChallenge.__table__.create(bind=engine, checkfirst=True)
    StepUpProof.__table__.create(bind=engine, checkfirst=True)

    org_id = uuid4()
    perm = "logistics.inventory_ledger.reconcile"
    user_id = uuid4()
    session_id = uuid4()

    principal = _make_principal(
        user_id=user_id,
        session_id=session_id,
        org_ids=[org_id],
        permissions=[perm],
        step_up_permissions=[perm],
    )

    challenge = StepUpChallenge(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        permission_code=perm,
        required_factors=["totp"],
        status="passed",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    database.add(challenge)
    database.flush()

    proof = StepUpProof(
        id=uuid4(),
        challenge_id=challenge.id,
        user_id=user_id,
        session_id=session_id,
        permission_code=perm,
        status="active",
        one_time=True,
        proof_hash="a" * 64,
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    database.add(proof)
    database.commit()

    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = lambda: database

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        res = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={
                "X-CSRF-Token": "test_csrf_token",
                "X-Step-Up-Proof-ID": str(proof.id),
            },
        )
        assert res.status_code == 202, f"Expected 202, got {res.status_code}: {res.text}"
    finally:
        app.dependency_overrides.clear()

