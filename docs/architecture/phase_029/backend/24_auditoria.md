# 24 — Catálogo de Eventos de Auditoría (`logistics_audit_events`)

## Registro Centrado en Auditoría y Trazabilidad

Todas las acciones críticas realizadas sobre el Maestro de Conductores se registran de forma síncrona en la tabla centralizada de eventos de auditoría `logistics_audit_events`.

---

## Catálogo de los 15 Eventos de Auditoría de la Fase 029

| # | Evento Auditado (`event_type`) | Severidad | Descripción del Disparador |
|---|---|---|---|
| 1 | **`DRIVER_CREATED`** | `INFO` | Creación de nuevo expediente de conductor. |
| 2 | **`DRIVER_UPDATED`** | `INFO` | Modificación de datos generales o de contacto. |
| 3 | **`DRIVER_LIFECYCLE_CHANGED`** | `WARN` | Cambio de estado de ciclo de vida (ej. `ACTIVE` -> `SUSPENDED`). |
| 4 | **`DRIVER_COMPLIANCE_CHANGED`** | `WARN` | Recálculo de cumplimiento (ej. `COMPLIANT` -> `EXPIRED`). |
| 5 | **`DRIVER_ELIGIBILITY_CHANGED`** | `CRITICAL` | Cambio en elegibilidad (ej. `ELIGIBLE` -> `INELIGIBLE`). |
| 6 | **`DRIVER_IDENTITY_DOC_ADDED`** | `INFO` | Adición de nuevo DNI/CE/Pasaporte. |
| 7 | **`DRIVER_LICENSE_ADDED`** | `INFO` | Registro o renovación de Licencia de Conducir. |
| 8 | **`DRIVER_LICENSE_CATEGORY_ASSIGNED`**| `INFO` | Asignación de categoría MTC (A-I, A-IIIb, etc.). |
| 9 | **`DRIVER_LICENSE_RESTRICTION_ADDED`**| `WARN` | Anotación de restricción en licencia (lentes, automática). |
| 10| **`DRIVER_PHOTO_UPLOADED`** | `INFO` | Carga de nueva fotografía o escaneo de licencia. |
| 11| **`DRIVER_DOCUMENT_ADDED`** | `INFO` | Carga de certificado Hazmat, Manejo Defensivo o Aptitud Médica. |
| 12| **`DRIVER_OP_RESTRICTION_APPLIED`** | `CRITICAL` | Imposición de bloqueo o sanción administrativa. |
| 13| **`DRIVER_OP_RESTRICTION_REVOKED`** | `CRITICAL` | Levantar / revocar sanción administrativa. |
| 14| **`DRIVER_SENSITIVE_DATA_REVEALED`**| `CRITICAL` | Revelación sin enmascarar de DNI / Licencia mediante Step-Up. |
| 15| **`DRIVER_USER_LINKED`** | `INFO` | Enlace u opcional de cuenta de usuario (`User`). |

---

## Estructura del Payload de Auditoría

```json
{
  "event_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
  "organization_id": "3c0b1e42-9f8a-4d76-b183-5c2009a712f1",
  "event_type": "DRIVER_OP_RESTRICTION_APPLIED",
  "actor_user_id": "99887766-5544-3322-1100-aabbccddeeff",
  "target_entity_type": "DriverModel",
  "target_entity_id": "8f8b89e3-4f3b-48c9-94b2-03f90b17849e",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "payload": {
    "driver_code": "DRV-000042",
    "restriction_type": "ALCOHOL_TEST_FAILURE",
    "severity": "PERMANENT_BLOCK",
    "reason": "Prueba de alcoholemia positiva en control pre-despacho (0.35 g/l)",
    "previous_eligibility": "ELIGIBLE",
    "new_eligibility": "INELIGIBLE"
  },
  "timestamp": "2026-07-29T00:43:20Z"
}
```
