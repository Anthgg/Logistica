# 22. Cobertura de Pruebas de Integración y API REST

## 1. Suite de Pruebas de Integración (End-to-End API)

Las pruebas de integración evalúan el comportamiento completo desde la llamada HTTP en FastAPI, pasando por la verificación de permisos RBAC, evaluación del motor en grafo, descomposición jerárquica y persistencia en base de datos PostgreSQL real.

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_packaging_decomposition_flow(async_client: AsyncClient, auth_headers_admin):
    """
    Prueba de integración: Crear jerarquía de empaques para un producto y evaluar descomposición API.
    1 PALLET = 40 CAJAS
    1 CAJA = 4 PAQUETES
    1 PAQUETE = 6 UND
    Entrada: 985 UND -> Esperado: 2 PALLETS, 9 CAJAS, 0 PAQUETES, 1 UND SUELTA.
    """
    product_id = "8f3b2a11-0000-4000-8000-000000000001"
    
    # 1. Solicitar descomposición vía REST API
    response = await async_client.post(
        "/api/logistics/unit-conversions/decompose",
        headers=auth_headers_admin,
        json={
            "product_id": product_id,
            "base_quantity": "985.000000000000000000"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["input_quantity"] == "985.000000000000000000"
    assert data["loose_base_units"] == "1.000000000000000000"
    
    decomp = data["decomposition"]
    assert len(decomp) == 2
    assert decomp[0]["packaging_unit_code"] == "PALLET"
    assert decomp[0]["package_count"] == 2
    assert decomp[1]["packaging_unit_code"] == "CAJA"
    assert decomp[1]["package_count"] == 9

@pytest.mark.asyncio
async def test_step_up_authentication_enforcement(async_client: AsyncClient, auth_headers_user):
    """
    Verifica que intentar crear una regla de conversión sin X-Step-Up-Token retorne 401.
    """
    response = await async_client.post(
        "/api/logistics/unit-conversion-rules",
        headers=auth_headers_user, # Token JWT normal sin Step-Up
        json={
            "from_unit_id": "...",
            "to_unit_id": "...",
            "conversion_factor": "100.0"
        }
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "STEP_UP_REQUIRED"
```

---

## 2. Verificación Multi-Tenant

Se ejecutan escenarios donde dos organizaciones independientes (`Org A` y `Org B`) definen reglas contradictorias para la misma unidad personalizada (ej. `Org A` define 1 TAMBOR = 200 L, `Org B` define 1 TAMBOR = 208 L). 

Las pruebas confirman que los datos y grafos están totalmente aislados por `organization_id` sin contaminación cruzada.
