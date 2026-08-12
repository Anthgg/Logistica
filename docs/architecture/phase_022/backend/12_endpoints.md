# 12. Especificación Completa de Endpoints REST / OpenAPI

## Resumen de la API de Almacenes y Ubicaciones

Todos los endpoints están expuestos bajo el prefijo `/api/logistics/warehouses` y requieren autenticación Bearer JWT. Operaciones críticas requieren Step-Up Authentication.

---

## Catálogo Resumido de Endpoints

| Método | Ruta | Permiso Requerido | Step-Up | Descripción |
| :--- | :--- | :--- | :---: | :--- |
| `GET` | `/` | `logistics.warehouses.read` | No | Lista paginada de almacenes de la organización. |
| `POST` | `/` | `logistics.warehouses.manage` | **SÍ** | Crea un nuevo almacén. |
| `GET` | `/{id}` | `logistics.warehouses.read` | No | Obtiene detalle extendido de un almacén. |
| `PUT` | `/{id}` | `logistics.warehouses.manage` | No | Actualiza datos operacionales del almacén. |
| `GET` | `/{id}/locations` | `logistics.warehouses.read` | No | Lista o busca árbol de ubicaciones. |
| `POST` | `/{id}/locations` | `logistics.warehouse_locations.create` | No | Crea una ubicación individual. |
| `GET` | `/{id}/locations/{loc_id}` | `logistics.warehouses.read` | No | Detalle de ubicación (capacidades + restricciones). |
| `PUT` | `/{id}/locations/{loc_id}` | `logistics.warehouse_locations.manage` | No | Actualiza datos de una ubicación. |
| `DELETE`| `/{id}/locations/{loc_id}` | `logistics.warehouse_locations.manage` | **SÍ** | Elimina una ubicación (sin hijos ni stock). |
| `POST` | `/{id}/locations/bulk-preview` | `logistics.warehouse_locations.create` | No | Vista previa de generación masiva. |
| `POST` | `/{id}/locations/bulk-generate` | `logistics.warehouse_locations.create` | No | Ejecuta generación masiva de ubicaciones. |
| `POST` | `/{id}/locations/{loc_id}/move-preview` | `logistics.warehouse_locations.move` | No | Simula el movimiento de un subárbol. |
| `POST` | `/{id}/locations/{loc_id}/move` | `logistics.warehouse_locations.move` | **SÍ** | Ejecuta el movimiento de un subárbol. |
| `GET` | `/{id}/logical-map` | `logistics.warehouses.read` | No | Payload 2D para renderizado React. |
| `POST` | `/{id}/layouts` | `logistics.warehouse_layouts.activate` | **SÍ** | Crea o activa una nueva versión del layout 2D. |
| `POST` | `/locations/resolve-qr` | `logistics.warehouses.read` | No | Resuelve payload opaco escaneado `t1loc:v1:...`. |
| `GET` | `/{id}/locations/{loc_id}/qr-image` | `logistics.warehouses.read` | No | Retorna imagen PNG binaria del código QR. |
| `POST` | `/{id}/locations/{loc_id}/rotate-qr` | `logistics.warehouses.manage` | **SÍ** | Rota la referencia opaca del QR. |
| `GET` | `/{id}/locations/{loc_id}/label-pdf` | `logistics.warehouses.read` | No | Descarga etiqueta PDF individual. |
| `POST` | `/{id}/locations/labels-batch-pdf` | `logistics.warehouses.read` | No | Descarga lote multipágina de etiquetas PDF. |

---

## Especificaciones de Payloads y Respuestas

### 1. `POST /api/logistics/warehouses/{id}/locations`
**Request Body:**
```json
{
  "parent_id": "c3a9d2e1-4567-89ab-cdef-0123456789ab",
  "code": "Z01",
  "name": "Zona Almacenamiento Frío",
  "location_type": "ZONE",
  "status": "ACTIVE",
  "is_pickable": true,
  "is_receivable": true,
  "capacity": {
    "max_weight_kg": 25000.0,
    "max_volume_cubic_meters": 150.0,
    "max_pallets": 50
  },
  "restrictions": [
    {
      "restriction_type": "COLD_CHAIN",
      "severity": "HARD_BLOCK",
      "min_temperature_celsius": 2.0,
      "max_temperature_celsius": 8.0
    }
  ]
}
```

**Response (HTTP 201 Created):**
```json
{
  "id": "e4f5a6b7-1234-5678-9abc-def012345678",
  "organization_id": "99999999-9999-9999-9999-999999999999",
  "warehouse_id": "8f3b2a11-9c8e-4b7d-a123-456789abcdef",
  "parent_id": "c3a9d2e1-4567-89ab-cdef-0123456789ab",
  "code": "Z01",
  "full_code": "ALM01-Z01",
  "name": "Zona Almacenamiento Frío",
  "location_type": "ZONE",
  "status": "ACTIVE",
  "hierarchy_path": "/c3a9d2e1-4567-89ab-cdef-0123456789ab/e4f5a6b7-1234-5678-9abc-def012345678",
  "depth": 1,
  "public_ref": "a8f9c1e2b4d543219876543210abcdef",
  "created_at": "2026-07-28T12:00:00Z"
}
```

---

### 2. `POST /api/logistics/locations/resolve-qr`
**Request Body:**
```json
{
  "qr_payload": "t1loc:v1:a8f9c1e2b4d543219876543210abcdef"
}
```

**Response (HTTP 200 OK):**
```json
{
  "status": "SUCCESS",
  "location": {
    "id": "e4f5a6b7-1234-5678-9abc-def012345678",
    "full_code": "ALM01-Z01",
    "warehouse_code": "ALM01",
    "name": "Zona Almacenamiento Frío",
    "status": "ACTIVE",
    "is_pickable": true
  }
}
```
