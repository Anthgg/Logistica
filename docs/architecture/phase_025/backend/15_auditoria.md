# 15. Registro e Eventos de Auditoría Inmutable

## Arquitectura de Auditoría en `logistics_audit_events`

Toda mutación de datos, cambio de estado, advertencia de duplicado o verificación de documentos dentro de la Fase 025 emite de forma sincrónica un evento inmutable hacia la tabla central `logistics_audit_events`.

Cada registro almacena el contexto de seguridad (usuario, organización, IP, Step-Up token utilizado) y la huella digital del estado previo y posterior en formato JSONB.

---

## Catálogo de los 18 Eventos de Auditoría

| # | Código del Evento (`event_type`) | Categoría | Descripción Operativa |
|---|----------------------------------|-----------|-----------------------|
| 1 | `BP_CREATED` | Creación | Creación de una nueva cabecera de socio de negocio. |
| 2 | `BP_UPDATED` | Modificación | Modificación de datos generales (razón social, nombre comercial). |
| 3 | `BP_STATUS_ACTIVATED` | Estado | Cambio de estado de cabecera a `ACTIVE`. |
| 4 | `BP_STATUS_SUSPENDED` | Estado | Suspensión temporal administrativa de la cabecera. |
| 5 | `BP_STATUS_BLOCKED` | Estado | Bloqueo preventivo de seguridad (requirió Step-Up Auth). |
| 6 | `BP_STATUS_ARCHIVED` | Estado | Desactivación lógica definitiva por inactividad. |
| 7 | `BP_ROLE_ASSIGNED` | Roles | Asignación de un nuevo rol (`SUPPLIER`, `CUSTOMER`, `CARRIER`). |
| 8 | `BP_ROLE_SUSPENDED` | Roles | Suspensión aislada de un rol específico. |
| 9 | `BP_ROLE_REACTIVATED` | Roles | Reactivación de un rol previamente suspendido. |
| 10 | `BP_PROFILE_UPDATED` | Perfiles | Actualización de perfil relacional (línea de crédito, lead time). |
| 11 | `BP_ADDRESS_CREATED` | Direcciones | Registro de nueva dirección física o fiscal. |
| 12 | `BP_ADDRESS_SET_PRIMARY` | Direcciones | Conmutación del flag de dirección primaria. |
| 13 | `BP_CONTACT_CREATED` | Contactos | Registro de un nuevo contacto operativo. |
| 14 | `BP_DOCUMENT_UPLOADED` | Documentación | Carga de expediente digital (Ficha RUC, Licencias). |
| 15 | `BP_DOCUMENT_VERIFIED` | Documentación | Verificación y aprobación de expediente legal. |
| 16 | `BP_EVALUATION_COMPLETED` | Evaluaciones | Registro de evaluación ponderada de desempeño aprobada. |
| 17 | `BP_DUPLICATE_FLAGGED` | Detección | Detección de posible duplicado por coincidencia fuzzy. |
| 18 | `BP_DUPLICATE_OVERRIDDEN` | Detección | Exención manual aprobada para crear socio con advertencia de duplicado. |

---

## Estructura de Payload del Evento en Audit Log

```json
{
  "event_id": "c71a39f6-1d11-4a11-b21a-289d81d21102",
  "event_type": "BP_STATUS_BLOCKED",
  "aggregate_type": "BUSINESS_PARTNER",
  "aggregate_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "organization_id": "3a0b12cd-8f44-482a-a309-881a17684021",
  "actor_user_id": "e44d9f65-2111-4822-b519-019d88192801",
  "step_up_authenticated": true,
  "timestamp": "2026-07-28T14:32:10.124552Z",
  "client_ip": "190.235.12.45",
  "changes": {
    "previous_status": "ACTIVE",
    "new_status": "BLOCKED",
    "block_reason": "RUC reportado en lista de contribuyentes No Habidos por SUNAT"
  }
}
```
