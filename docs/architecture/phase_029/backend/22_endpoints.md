# 22 — Especificación de Endpoints REST / OpenAPI (`/api/logistics/drivers`)

## Catálogo Resumido de Endpoints

Todos los endpoints se exponen bajo el prefijo `/api/logistics/drivers` y requieren autenticación mediante JWT (`Bearer Token`) y control de acceso RBAC.

| Método HTTP | Ruta Endpoint | Descripción Operativa | Permiso Requerido |
|---|---|---|---|
| **`GET`** | `/api/logistics/drivers` | Listar y filtrar conductores (con paginación y búsqueda). | `logistics.drivers.read` |
| **`POST`** | `/api/logistics/drivers` | Crear nuevo conductor (genera código `DRV-XXXXXX`). | `logistics.drivers.create` |
| **`GET`** | `/api/logistics/drivers/{id}` | Obtener detalle completo de un conductor por UUID. | `logistics.drivers.read` |
| **`PUT`** | `/api/logistics/drivers/{id}` | Actualizar datos básicos (con control `row_version`). | `logistics.drivers.update` |
| **`POST`** | `/api/logistics/drivers/{id}/sensitive-reveal` | Revelar DNI y Licencia sin enmascarar (Step-Up). | `logistics.drivers.sensitive.read` |
| **`POST`** | `/api/logistics/drivers/{id}/licenses` | Registrar / Renovar Licencia de Conducir. | `logistics.drivers.update` |
| **`POST`** | `/api/logistics/drivers/{id}/documents` | Cargar documento de capacitación / aptitud médica. | `logistics.drivers.update` |
| **`POST`** | `/api/logistics/drivers/{id}/restrictions` | Aplicar restricción operativa / sanción administrativa. | `logistics.drivers.restrictions.manage` |
| **`DELETE`** | `/api/logistics/drivers/{id}/restrictions/{r_id}`| Revocar restricción operativa. | `logistics.drivers.restrictions.revoke` |
| **`POST`** | `/api/logistics/drivers/{id}/evaluate-eligibility`| Forzar recálculo síncrono de cumplimiento y elegibilidad. | `logistics.drivers.read` |
| **`GET`** | `/api/logistics/drivers/{id}/versions` | Listar versiones e historial de snapshots JSONB. | `logistics.drivers.read` |
| **`POST`** | `/api/logistics/drivers/duplicate-check` | Evaluar riesgo de duplicados antes de guardar. | `logistics.drivers.read` |

---

## Especificaciones OpenAPI Representativas

### 1. `POST /api/logistics/drivers`

#### Request Payload:
```json
{
  "first_name": "Juan Carlos",
  "last_name": "Pérez Gómez",
  "date_of_birth": "1988-05-14",
  "gender": "MALE",
  "nationality": "PER",
  "identity_document": {
    "document_type": "DNI",
    "document_number": "72849153",
    "issuing_country": "PER"
  },
  "primary_license": {
    "license_number": "Q72849153",
    "issuing_authority": "MTC",
    "issued_at": "2020-06-10",
    "expires_at": "2028-06-10",
    "category_codes": ["A-IIIb"],
    "restrictions": [
      {
        "code": "REST_CORRECTIVE_LENSES",
        "description": "Uso obligatorio de lentes",
        "severity": "INFORMATIONAL"
      }
    ]
  }
}
```

#### Response (201 Created):
```json
{
  "id": "8f8b89e3-4f3b-48c9-94b2-03f90b17849e",
  "organization_id": "3c0b1e42-9f8a-4d76-b183-5c2009a712f1",
  "driver_code": "DRV-000042",
  "normalized_driver_code": "DRV-000042",
  "display_name": "Juan Carlos Pérez Gómez",
  "lifecycle_status": "PENDING_VERIFICATION",
  "compliance_status": "COMPLIANT",
  "eligibility_status": "ELIGIBLE",
  "identity_documents": [
    {
      "document_type": "DNI",
      "masked_document_number": "*****153",
      "verification_status": "UNVERIFIED"
    }
  ],
  "primary_license": {
    "masked_license_number": "****9153",
    "status": "VALID",
    "expires_at": "2028-06-10"
  },
  "row_version": 1,
  "created_at": "2026-07-29T00:41:22Z"
}
```

---

### 2. `POST /api/logistics/drivers/{id}/sensitive-reveal`

#### Request Payload:
```json
{
  "step_up_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "reason": "Auditoría en Garita de Control Norte - Emisión de Manifiesto"
}
```

#### Response (200 OK):
```json
{
  "driver_id": "8f8b89e3-4f3b-48c9-94b2-03f90b17849e",
  "unmasked_identity_document": "72849153",
  "unmasked_license_number": "Q72849153",
  "revealed_at": "2026-07-29T00:45:00Z",
  "audit_event_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
}
```
