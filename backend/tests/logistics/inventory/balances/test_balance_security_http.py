"""
test_balance_security_http.py — Seguridad HTTP real (Fase 045)

CRITERIO DE EVIDENCIA:
- TestClient real contra la aplicación FastAPI real
- Rutas exactas extraídas de app.openapi() (no búsqueda vaga)
- Verificar BALANCES_BASE_PATH real desde código (no asumido)
- GET sin autenticación → 401 o 403
- POST rebuild sin CSRF header → 401/403/422
- Endpoints prohibidos → 404
- Route collisions verificadas
- BLOCKED_AUTH_TEST_FIXTURES_MISSING: documentado para RBAC/step-up completo
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.security

# ---------------------------------------------------------------------------
# Configuración de paths — extraídos del código real, no asumidos
# ---------------------------------------------------------------------------

# Reconstruido desde código fuente real:
# app.main → api_router(prefix=/api) → logistics_router(prefix=/logistics)
# → inventory_balances_router(prefix=/inventory) → router(prefix=/balances)
_BALANCES_BASE_PATH = "/api/logistics/inventory/balances"
_API_PREFIX = "/api"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.security
def test_openapi_balances_paths_exact():
    """
    OPENAPI_EXACT — Extrae paths reales de app.openapi() y verifica
    BALANCES_BASE_PATH exacto.

    Criterio: no usar búsqueda vaga 'if "balances" in path'.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema.get("paths", {})

    # Extraer exactamente los paths de balances
    balance_paths = sorted([p for p in paths if _BALANCES_BASE_PATH in p])
    assert len(balance_paths) > 0, (
        f"OPENAPI FAIL: No se encontraron paths con '{_BALANCES_BASE_PATH}' en OpenAPI. "
        f"Paths inventario encontrados: {[p for p in paths if 'inventory' in p]}"
    )

    # Reportar paths reales encontrados
    print(f"\nBALANCES_PATHS encontrados en OpenAPI: {balance_paths}")

    # Verificar que NO hay route collision con doble prefijo
    collision_patterns = [
        "/api/logistics/inventory/inventory/balances",
        "/api/logistics/balances",
        "/api/v1/logistics/inventory/balances",
    ]
    for collision in collision_patterns:
        assert not any(p.startswith(collision) for p in paths), (
            f"ROUTE_COLLISION DETECTED: El path '{collision}' existe en OpenAPI. "
            f"Verificar montaje de routers."
        )


@pytest.mark.security
def test_no_api_v1_prefix_in_balances():
    """
    API_PREFIX VERIFICATION — Confirma que el prefijo real es /api (no /api/v1).

    El prefijo /api/v1 nunca existió en config.py. Este test confirma
    que los tests anteriores usaban el prefijo correcto.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/openapi.json")
    schema = response.json()
    paths = list(schema.get("paths", {}).keys())

    # Ningún path debe empezar con /api/v1
    v1_paths = [p for p in paths if p.startswith("/api/v1")]
    assert len(v1_paths) == 0, (
        f"API_PREFIX ANOMALY: Se encontraron paths con /api/v1 en OpenAPI: {v1_paths}. "
        f"La configuración real usa API_PREFIX=/api."
    )

    # Sí deben existir paths con /api
    api_paths = [p for p in paths if p.startswith("/api")]
    assert len(api_paths) > 0, "FAIL: No hay paths con prefijo /api en OpenAPI"


@pytest.mark.security
def test_forbidden_endpoints_return_404():
    """
    FORBIDDEN_ENDPOINTS — Endpoints de mutación directa de saldo no deben existir.

    Estos endpoints están prohibidos por arquitectura:
    - set-stock
    - fix-stock
    - force-balance
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
            f"FORBIDDEN_ENDPOINT DETECTED: '{path}' existe y respondió "
            f"HTTP {res.status_code} (esperado 404)."
        )


@pytest.mark.security
def test_unauthenticated_get_balance_summary_is_denied():
    """
    RBAC_READ — GET a /balances/summary sin autenticación debe ser rechazado.

    La aplicación real usa session cookies con autenticación continua.
    Sin credenciales válidas, el endpoint debe retornar 401 o 403.

    BLOCKED_AUTH_TEST_FIXTURES_MISSING:
    No se puede probar login completo + RBAC + Step-up porque el sistema de auth
    usa cookies HttpOnly con flujo CSRF y no hay fixtures de usuario de test.
    Se documenta el bloqueo honestamente según la regla absoluta de evidencia.
    """
    client = TestClient(app, raise_server_exceptions=False)
    from uuid import uuid4
    response = client.get(
        f"{_BALANCES_BASE_PATH}/summary",
        params={"organization_id": str(uuid4())},
    )
    # Sin autenticación debe ser 401 o 403 (no 200, no 500)
    assert response.status_code in (401, 403), (
        f"RBAC FAIL: GET /summary sin auth respondió HTTP {response.status_code}. "
        f"Se esperaba 401 o 403. "
        f"Body: {response.text[:200]}"
    )


@pytest.mark.security
def test_unauthenticated_post_rebuild_is_denied():
    """
    RBAC_REBUILD — POST a /balances/rebuild sin autenticación debe ser rechazado.
    """
    from uuid import uuid4
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        f"{_BALANCES_BASE_PATH}/rebuild",
        json={
            "organization_id": str(uuid4()),
            "rebuild_mode": "FULL",
        },
    )
    assert response.status_code in (401, 403), (
        f"RBAC FAIL: POST /rebuild sin auth respondió HTTP {response.status_code}. "
        f"Se esperaba 401 o 403. "
        f"Body: {response.text[:200]}"
    )


@pytest.mark.security
def test_route_collision_does_not_exist():
    """
    ROUTE_COLLISION — Verificar que no exista doble prefijo /inventory/inventory.
    """
    client = TestClient(app, raise_server_exceptions=False)
    # Si existe route collision /inventory/inventory/balances → el router está mal montado
    response = client.get("/api/logistics/inventory/inventory/balances/summary")
    assert response.status_code == 404, (
        f"ROUTE_COLLISION DETECTED: /api/logistics/inventory/inventory/balances/summary "
        f"respondió HTTP {response.status_code} (esperado 404). "
        f"El router de balances está montado con doble prefijo /inventory."
    )


@pytest.mark.security
def test_blocked_rbac_csrf_stepup_documented():
    """
    BLOCKED_AUTH_TEST_FIXTURES_MISSING — Documentación de bloqueo honesto.

    Los siguientes controles NO pueden ser verificados en esta fase porque
    el sistema de autenticación real requiere:
    - Login con credenciales reales + cookie HttpOnly
    - CSRF token generado por el servidor
    - Step-up con flujo de elevación real

    No existen fixtures de test que provean sesión autenticada real.
    Los tests siguientes están documentados como BLOCKED:

    BLOCKED: RBAC_READ con usuario autenticado + permiso válido → 200
    BLOCKED: RBAC_READ con usuario sin permiso → 403
    BLOCKED: RBAC_REBUILD con permiso read pero sin rebuild → 403
    BLOCKED: CSRF POST con cookie + header correcto → pasa
    BLOCKED: CSRF POST sin header → rechazado
    BLOCKED: STEP_UP_REQUIRED para rebuild sin elevación
    BLOCKED: CROSS_TENANT GET → 403/404

    Resolución: Crear fixtures de autenticación de test (usuario_test, org_test)
    en un conftest dedicado de seguridad para desbloquear estos controles.
    """
    pytest.skip(
        "BLOCKED_AUTH_TEST_FIXTURES_MISSING: "
        "No existen fixtures de sesión autenticada para probar "
        "RBAC, CSRF y Step-up via HTTP real. "
        "Ver docstring para lista completa de controles bloqueados."
    )
