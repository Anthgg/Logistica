# 16. Especificación Detallada de Endpoints REST / OpenAPI

## 1. Mapa de Endpoints REST del Módulo de Unidades y Conversiones

Todos los endpoints están prefijados bajo la ruta base del API Gateway `/api/logistics` y requieren autenticación Bearer JWT.

| Método HTTP | Endpoint | Descripción | RBAC Permiso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/logistics/measurement-dimensions` | Listar catálogo de dimensiones físicas. | `logistics.units.read` |
| `GET` | `/api/logistics/measurement-dimensions/{id}` | Obtener detalle de dimensión física. | `logistics.units.read` |
| `GET` | `/api/logistics/units` | Listar maestro de UOMs (filtrado por scope/dimensión). | `logistics.units.read` |
| `POST` | `/api/logistics/units` | Crear unidad de medida personalizada. | `logistics.units.manage` (Step-Up) |
| `GET` | `/api/logistics/units/{id}` | Obtener detalle de unidad de medida. | `logistics.units.read` |
| `PUT` | `/api/logistics/units/{id}` | Actualizar unidad de medida. | `logistics.units.manage` (Step-Up) |
| `DELETE` | `/api/logistics/units/{id}` | Desactivación lógica de unidad. | `logistics.units.manage` (Step-Up) |
| `GET` | `/api/logistics/unit-conversion-rules` | Listar reglas de conversión física. | `logistics.unit_conversions.read` |
| `POST` | `/api/logistics/unit-conversion-rules` | Crear nueva regla de conversión física. | `logistics.unit_conversions.manage` (Step-Up) |
| `GET` | `/api/logistics/products/{id}/unit-configuration` | Obtener configuración de 5 unidades de producto. | `logistics.product_units.read` |
| `PUT` | `/api/logistics/products/{id}/unit-configuration` | Configurar/Actualizar unidades de proceso de producto. | `logistics.product_units.manage` |
| `GET` | `/api/logistics/products/{id}/packaging-definitions` | Obtener árbol jerárquico de empaques de producto. | `logistics.product_units.read` |
| `POST` | `/api/logistics/products/{id}/packaging-definitions` | Crear/Añadir nivel de empaque a producto. | `logistics.product_units.manage` (Step-Up) |
| `POST` | `/api/logistics/unit-conversions/evaluate` | Evaluar conversión entre dos unidades (Core Engine). | `logistics.unit_conversions.read` |
| `POST` | `/api/logistics/unit-conversions/decompose` | Descomponer cantidad base en estructura de empaques. | `logistics.unit_conversions.read` |
| `POST` | `/api/logistics/unit-conversions/compare` | Comparar equivalencia entre dos cantidades en UOMs distintas.| `logistics.unit_conversions.read` |

---

## 2. Ejemplos de Payloads OpenAPI 3.0

### Endpoint: `POST /api/logistics/unit-conversions/evaluate`

#### Request Body:
```json
{
  "from_unit_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0001",
  "to_unit_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0002",
  "quantity": "25.500000000000000000",
  "product_id": "8f3b2a11-0000-4000-8000-000000000001",
  "rounding_policy": "HALF_UP",
  "target_scale": 2
}
```

#### Response 200 OK:
```json
{
  "from_unit_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0001",
  "to_unit_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0002",
  "input_quantity": "25.500000000000000000",
  "exact_result": "612.000000000000000000",
  "rounded_result": "612.000000000000000000",
  "residual": "0.000000000000000000",
  "effective_factor": "24.000000000000000000",
  "path_hops": [
    {
      "hop_index": 1,
      "from_unit_code": "CAJA",
      "to_unit_code": "UND",
      "rule_source": "PRODUCT_PACKAGING",
      "factor": "24.000000000000000000"
    }
  ],
  "rounding_policy_applied": "HALF_UP"
}
```

---

### Endpoint: `POST /api/logistics/unit-conversions/decompose`

#### Request Body:
```json
{
  "product_id": "8f3b2a11-0000-4000-8000-000000000001",
  "base_quantity": "985.000000000000000000"
}
```

#### Response 200 OK:
```json
{
  "product_id": "8f3b2a11-0000-4000-8000-000000000001",
  "input_quantity": "985.000000000000000000",
  "base_unit_code": "UND",
  "decomposition": [
    {
      "hierarchy_level": 3,
      "packaging_unit_code": "PALLET",
      "package_count": 2,
      "equivalent_base_quantity": "768.000000000000000000"
    },
    {
      "hierarchy_level": 2,
      "packaging_unit_code": "CAJA",
      "package_count": 9,
      "equivalent_base_quantity": "216.000000000000000000"
    }
  ],
  "loose_base_units": "1.000000000000000000",
  "total_decomposed_base_units": "985.000000000000000000"
}
```
