# Especificación REST / OpenAPI de Endpoints

## 1. Resumen de Endpoints de la Fase 027

Todos los endpoints están prefijados con la versión API `/api/v1/logistics`. Exigen autenticación Bearer JWT y validan permisos RBAC del usuario.

| Método | Endpoint | Descripción | Permiso Requerido | Step-Up Auth |
|---|---|---|---|---|
| `GET` | `/api/v1/logistics/vehicles` | Listar y buscar vehículos paginados | `logistics.vehicles.read` | No |
| `POST` | `/api/v1/logistics/vehicles` | Crear un nuevo vehículo | `logistics.vehicles.create` | No |
| `GET` | `/api/v1/logistics/vehicles/{id}` | Obtener detalle completo de un vehículo | `logistics.vehicles.read` | No |
| `PUT` | `/api/v1/logistics/vehicles/{id}` | Actualizar datos generales | `logistics.vehicles.update` | No |
| `POST` | `/api/v1/logistics/vehicles/{id}/change-plate` | Reasignar placa de vehículo | `logistics.vehicles.change_plate` | **Sí** |
| `POST` | `/api/v1/logistics/vehicles/{id}/capacity` | Definir/actualizar perfil de capacidades | `logistics.vehicles.update` | No |
| `POST` | `/api/v1/logistics/vehicles/{id}/dimensions` | Definir/actualizar dimensiones físicas | `logistics.vehicles.update` | No |
| `POST` | `/api/v1/logistics/vehicles/{id}/documents` | Registrar nuevo documento en expediente | `logistics.vehicles.documents.create` | No |
| `GET` | `/api/v1/logistics/vehicles/{id}/documents` | Listar expediente documental | `logistics.vehicles.read` | No |
| `POST` | `/api/v1/logistics/vehicles/{id}/block` | Imponer restricción / bloqueo manual | `logistics.vehicles.block` | **Sí** |
| `POST` | `/api/v1/logistics/vehicles/{id}/unblock` | Resolver y retirar bloqueo manual | `logistics.vehicles.unblock` | **Sí** |
| `GET` | `/api/v1/logistics/vehicles/{id}/versions` | Listar historial de snapshots SHA-256 | `logistics.vehicles.audit` | No |
| `GET` | `/api/v1/logistics/vehicle-makes` | Catálogo de marcas | `logistics.vehicles.read` | No |
| `POST` | `/api/v1/logistics/vehicle-makes` | Crear marca custom | `logistics.vehicles.create` | No |
| `GET` | `/api/v1/logistics/vehicle-models` | Catálogo de modelos | `logistics.vehicles.read` | No |

---

## 2. Detalles de Endpoints Críticos

### 2.1 `POST /api/v1/logistics/vehicles`

#### Body Request:
```json
{
  "vehicle_code": "FL-104",
  "display_plate": "A1B-890",
  "vin": "19VDE1F28GE012345",
  "make_id": "8f31b412-2244-484d-b054-e0c19b02a110",
  "model_id": "9a12c334-1122-3344-5566-778899aabbcc",
  "vehicle_type": "RIGID_TRUCK",
  "body_type": "DRY_VAN",
  "chassis_number": "CH-9988112",
  "engine_number": "ENG-4455221"
}
```

#### Response (201 Created):
```json
{
  "id": "e4a3b2c1-0011-2233-4455-66778899aabb",
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "vehicle_code": "FL-104",
  "normalized_vehicle_code": "FL104",
  "display_plate": "A1B-890",
  "normalized_plate": "A1B890",
  "vin": "19VDE1F28GE012345",
  "normalized_vin": "19VDE1F28GE012345",
  "vehicle_type": "RIGID_TRUCK",
  "body_type": "DRY_VAN",
  "lifecycle_status": "DRAFT",
  "operational_status": "UNAVAILABLE",
  "compliance_status": "PENDING_REVIEW",
  "row_version": 1,
  "created_at": "2026-07-28T21:50:00Z"
}
```

---

### 2.2 `POST /api/v1/logistics/vehicles/{id}/change-plate`

#### Headers:
`X-Step-Up-Token`: Token proveniente del flujo MDU/FIDO2 o TOTP de la autenticación continua.

#### Body Request:
```json
{
  "new_plate": "F3X-992",
  "reason": "Re-matriculación SUNARP por cambio de uso a transporte público de mercadería."
}
```

#### Response (200 OK):
```json
{
  "vehicle_id": "e4a3b2c1-0011-2233-4455-66778899aabb",
  "previous_plate": "A1B-890",
  "new_plate": "F3X-992",
  "alias_created": "A1B-890",
  "version_number": 2,
  "content_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
  "updated_at": "2026-07-28T21:55:00Z"
}
```
