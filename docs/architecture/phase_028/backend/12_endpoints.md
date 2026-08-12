# Especificación de Endpoints REST / OpenAPI — Fase 028

## 1. Resumen de Rutas y Controladores

Todos los endpoints de la Fase 028 están expuestos bajo el prefijo `/api/v1/logistics`. Exigen autenticación JWT previa y validación de permisos RBAC granular.

```
/api/v1/logistics/vehicle-verification-sources
/api/v1/logistics/vehicle-verifications
/api/v1/logistics/assisted-verifications
/api/v1/logistics/vehicle-verification-conflicts
```

---

## 2. Endpoints de Fuentes de Verificación (`/vehicle-verification-sources`)

### 2.1. `GET /api/v1/logistics/vehicle-verification-sources`
Obtiene el catálogo de fuentes registradas y su estado de autorización.

* **Permiso RBAC**: `logistics.vehicle_verifications.read`
* **Query Parameters**:
  * `authorization_status` (opcional): `ACTIVE`, `MAINTENANCE`, `DEPRECATED`, `DISABLED`
* **Response `200 OK`**:
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "code": "SUNARP",
    "name": "Superintendencia Nacional de los Registros Públicos",
    "source_type": "GOVERNMENT_OFFICIAL",
    "priority": 1,
    "default_confidence_score": 1.00,
    "staleness_days": 30,
    "is_official_entity": true,
    "authorization_status": "ACTIVE"
  },
  {
    "id": "8cb12a99-1122-3344-5566-778899aabbcc",
    "code": "APESEG_SOAT",
    "name": "Asociación Peruana de Empresas de Seguros",
    "source_type": "INSURANCE_REGISTRY",
    "priority": 3,
    "default_confidence_score": 0.95,
    "staleness_days": 7,
    "is_official_entity": false,
    "authorization_status": "ACTIVE"
  }
]
```

---

## 3. Endpoints de Verificaciones Vehiculares (`/vehicle-verifications`)

### 3.1. `POST /api/v1/logistics/vehicle-verifications`
Inicia y ejecuta un nuevo proceso de verificación para una placa vehicular.

* **Permiso RBAC**: `logistics.vehicle_verifications.create`
* **Request Body**:
```json
{
  "vehicle_id": "c1f7b880-99aa-44bb-88cc-112233445566",
  "source_code": "SUNARP",
  "plate_number": "ABC-123"
}
```
* **Response `201 Created`**:
```json
{
  "verification_id": "a90184b2-3344-5566-7788-9900aabbccdd",
  "verification_number": "VER-20260728-98124",
  "vehicle_id": "c1f7b880-99aa-44bb-88cc-112233445566",
  "plate_number": "ABC-123",
  "status": "COMPLETED",
  "outcome_status": "VERIFIED_MATCH",
  "overall_confidence_score": 1.00,
  "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "conflicts_detected": 0,
  "verification_date": "2026-07-28T22:00:00Z",
  "expiration_date": "2026-08-27T22:00:00Z"
}
```

### 3.2. `GET /api/v1/logistics/vehicle-verifications/{id}`
Obtiene el detalle completo de una verificación, incluyendo provenance a nivel de campo.

* **Permiso RBAC**: `logistics.vehicle_verifications.read`
* **Response `200 OK`**:
```json
{
  "id": "a90184b2-3344-5566-7788-9900aabbccdd",
  "verification_number": "VER-20260728-98124",
  "status": "COMPLETED",
  "result": {
    "outcome_status": "VERIFIED_MATCH",
    "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "overall_confidence_score": 1.00,
    "execution_time_ms": 14
  },
  "field_provenance": [
    {
      "field_name": "vin",
      "raw_source_value": "1HGCR2F83HA001234",
      "normalized_value": "1HGCR2F83HA001234",
      "erp_current_value": "1HGCR2F83HA001234",
      "is_matching": true,
      "confidence_score": 1.00
    }
  ]
}
```

### 3.3. `POST /api/v1/logistics/vehicle-verifications/{id}/apply`
Aplica los datos verificados al vehículo y congela un snapshot inmutable. Requiere **Step-Up Authentication**.

* **Permiso RBAC**: `logistics.vehicle_verifications.apply`
* **Protección**: `Step-Up Authentication Required`
* **Response `200 OK`**:
```json
{
  "message": "Datos verificados aplicados exitosamente.",
  "version_snapshot": {
    "vehicle_id": "c1f7b880-99aa-44bb-88cc-112233445566",
    "version_number": 4,
    "version_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
    "applied_fields": ["vin", "engine_number", "manufacturing_year"]
  }
}
```

---

## 4. Endpoints de Verificación Asistida (`/assisted-verifications`)

### 4.1. `POST /api/v1/logistics/assisted-verifications`
Registra una verificación manual asistida con subida de evidencias probatorias.

* **Permiso RBAC**: `logistics.assisted_verifications.create`
* **Request Body (Multipart Form Data)**:
  * `vehicle_id`: UUID
  * `plate_number`: string
  * `operator_notes`: string
  * `owner_document`: string (DNI/RUC — se hashea internamente)
  * `owner_name`: string (se enmascara en UI)
  * `files`: List[UploadFile] (PDF/JPG Tarjeta de Propiedad, CITV, SOAT)
* **Response `201 Created`**:
```json
{
  "assisted_verification_id": "b1122334-4455-6677-8899-aabbccddeeff",
  "approval_status": "PENDING_APPROVAL",
  "masked_owner_name": "J*** P**** Z*****",
  "owner_identity_hash": "8f43b67c9600a941a54c0e620603f0d2c0b4a45a3c94c9d968b6b281f621d10e",
  "evidences_count": 2,
  "created_by": "user-uuid-1111"
}
```

### 4.2. `POST /api/v1/logistics/assisted-verifications/{id}/approve`
Aprueba una verificación asistida pendiente. Enforce **Segregación de Funciones**. Requiere **Step-Up Authentication**.

* **Permiso RBAC**: `logistics.assisted_verifications.approve`
* **Protección**: `Step-Up Authentication Required`
* **Response `200 OK`**:
```json
{
  "assisted_verification_id": "b1122334-4455-6677-8899-aabbccddeeff",
  "approval_status": "APPROVED",
  "approved_by": "supervisor-uuid-2222",
  "approval_date": "2026-07-28T22:15:00Z"
}
```

---

## 5. Endpoints de Conflictos de Verificación (`/vehicle-verification-conflicts`)

### 5.1. `GET /api/v1/logistics/vehicle-verification-conflicts`
Lista los conflictos de verificación registrados con filtros por severidad y estado.

* **Permiso RBAC**: `logistics.vehicle_verifications.read`
* **Query Parameters**:
  * `vehicle_id` (opcional): UUID
  * `status` (opcional): `OPEN`, `RESOLVED_OVERRIDDEN`, `RESOLVED_UPDATED`, `IGNORED`
  * `severity` (opcional): `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

### 5.2. `POST /api/v1/logistics/vehicle-verification-conflicts/{id}/resolve`
Resuelve manualmente un conflicto con justificación de compliance. Requiere **Step-Up Authentication**.

* **Permiso RBAC**: `logistics.vehicle_verifications.resolve_conflict`
* **Request Body**:
```json
{
  "action": "RESOLVED_OVERRIDDEN",
  "resolution_comment": "Se presenta certificado de rectificación de motor expedido por SUNARP."
}
```
* **Response `200 OK`**:
```json
{
  "conflict_id": "c9988776-5544-3322-1100-aabbccddeeff",
  "status": "RESOLVED_OVERRIDDEN",
  "resolved_by": "user-uuid-3333",
  "resolved_at": "2026-07-28T22:18:00Z"
}
```
