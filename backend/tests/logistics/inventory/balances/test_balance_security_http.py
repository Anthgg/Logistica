from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_schema_contains_inventory_balances_route():
    """Valida la presencia del router oficial de saldos en OpenAPI."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})

    balance_paths = [
        p for p in paths
        if "balances" in p and ("logistics" in p or "inventory" in p)
    ]
    assert len(balance_paths) > 0, "No se encontraron rutas con prefijo de balances en OpenAPI"


def test_forbidden_endpoints_do_not_exist():
    """Confirma que endpoints prohibidos como set-stock, fix-stock o force-balance NO existan."""
    forbidden = [
        "/api/logistics/inventory/balances/set-stock",
        "/api/logistics/inventory/balances/fix-stock",
        "/api/logistics/inventory/balances/force-balance",
    ]
    for path in forbidden:
        res = client.post(path, json={"balance": "999"})
        assert res.status_code == 404, f"Endpoint prohibido {path} existe y respondió {res.status_code}"


def test_numeric_precision_high_scale():
    """Verifica el soporte exacto de precisión Numeric(38,18) en Python Decimal."""
    small_val = Decimal("0.000000000000000001")
    large_val = Decimal("99999999999999999999.999999999999999999")

    assert f"{small_val:.18f}" == "0.000000000000000001"
    assert small_val == Decimal("0.000000000000000001")
    assert large_val == Decimal("99999999999999999999.999999999999999999")
    assert (small_val + Decimal("0.000000000000000001")) == Decimal("0.000000000000000002")
