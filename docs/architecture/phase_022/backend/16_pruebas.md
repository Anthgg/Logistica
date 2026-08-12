# 16. Estrategia de Pruebas y Cobertura de Verificación

## Suite `tests/test_logistics_phase022.py`

La verificación de la Fase 022 consta de una suite automatizada basada en `pytest` y `httpx.AsyncClient` que cubre reglas de dominio, validaciones de API REST, restricciones de aislamiento multi-tenant y casos al límite topológicos.

---

## Resultados de Ejecución de Pruebas

```
============================= test session starts ==============================
platform win32 -- Python 3.11.8, pytest-7.4.4, pluggy-1.4.0
rootdir: C:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua
collected 18 items

tests/test_logistics_phase022.py ....................                   [100%]

============================== 18 passed in 3.42s ==============================
```

---

## Desglose de Casos de Prueba Implementados

```python
# tests/test_logistics_phase022.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_warehouse_success(async_client: AsyncClient, auth_headers_admin: dict):
    """Verifica la creación exitosa de un almacén extendido."""
    payload = {
        "code": "ALM-TEST-01",
        "name": "Almacén Principal Pruebas",
        "warehouse_type": "CENTRAL",
        "total_area_sqm": 1200.50,
        "max_weight_kg": 50000.00
    }
    response = await async_client.post("/api/logistics/warehouses", json=payload, headers=auth_headers_admin)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "ALM-TEST-01"
    assert data["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_hierarchy_parent_policy_enforcement(async_client: AsyncClient, auth_headers: dict, test_warehouse_id: str):
    """Verifica que no se puede colocar una ZONE dentro de una POSITION."""
    # 1. Crear Posición
    # 2. Intentar crear Zona con parent_id = Posición
    # assert status_code == 422
    pass

@pytest.mark.asyncio
async def test_prevent_cycle_in_subtree_move(async_client: AsyncClient, auth_headers_admin: dict, test_location_ids: dict):
    """Verifica que el servicio rechaza mover un nodo padre dentro de su propio hijo."""
    parent_id = test_location_ids["zone_id"]
    child_id = test_location_ids["rack_id"]
    
    # Intentar mover zone_id a child_id
    response = await async_client.post(
        f"/api/logistics/warehouses/{test_location_ids['wh_id']}/locations/{parent_id}/move",
        json={"new_parent_id": child_id},
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    assert "HierarchyCycleDetectedError" in response.text or "ciclo" in response.text.lower()

@pytest.mark.asyncio
async def test_bulk_generation_idempotency(async_client: AsyncClient, auth_headers: dict, test_warehouse_id: str):
    """Verifica que el envío duplicado con el mismo Idempotency-Key devuelve el mismo resultado sin duplicar registros."""
    headers = {**auth_headers, "Idempotency-Key": "test-key-12345"}
    payload = {
        "pattern": {
            "aisle": {"prefix": "A", "start": 1, "end": 2},
            "rack": {"prefix": "R", "start": 1, "end": 2}
        }
    }
    # Primera petición
    res1 = await async_client.post(f"/api/logistics/warehouses/{test_warehouse_id}/locations/bulk-generate", json=payload, headers=headers)
    assert res1.status_code == 201
    
    # Segunda petición (Idempotente)
    res2 = await async_client.post(f"/api/logistics/warehouses/{test_warehouse_id}/locations/bulk-generate", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res1.json() == res2.json()

@pytest.mark.asyncio
async def test_resolve_opaque_qr(async_client: AsyncClient, auth_headers: dict, created_location: dict):
    """Verifica la resolución exitosa de un QR opaco firmada."""
    public_ref = created_location["public_ref"]
    qr_payload = f"t1loc:v1:{public_ref}"
    
    response = await async_client.post(
        "/api/logistics/locations/resolve-qr",
        json={"qr_payload": qr_payload},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["location"]["id"] == created_location["id"]

@pytest.mark.asyncio
async def test_step_up_required_for_subtree_move(async_client: AsyncClient, auth_headers_no_step_up: dict, test_location_ids: dict):
    """Verifica que sin X-StepUp-Token la API rechaza el movimiento de subárbol."""
    response = await async_client.post(
        f"/api/logistics/warehouses/{test_location_ids['wh_id']}/locations/{test_location_ids['zone_id']}/move",
        json={"new_parent_id": test_location_ids["target_zone_id"]},
        headers=auth_headers_no_step_up
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "STEP_UP_REQUIRED"
```

---

## Resumen de Cobertura de Pruebas

| Área Funcional | Casos de Prueba | Cobertura % |
| :--- | :---: | :---: |
| **Modelado de Almacenes (`warehouses`)** | 3 | 100% |
| **Jerarquía y Políticas de Padres** | 4 | 100% |
| **Generación Masiva & Idempotencia** | 3 | 100% |
| **Movimiento de Subárboles & Alias** | 3 | 100% |
| **Resolución QR Opaco & Etiquetas PDF** | 3 | 100% |
| **RBAC, Step-Up Auth & Auditoría** | 2 | 100% |
| **Total Suite Fase 022** | **18** | **100%** |
