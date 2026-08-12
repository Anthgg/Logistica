# Contrato de rutas API para el frontend

Verificado el 2026-08-02 contra:

- Cloud Run: `https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/openapi.json`
- Backend local: `app.main.app.openapi()`

## Regla de base URL

El cliente frontend debe configurar:

```text
https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api
```

Las rutas entregadas a `api-client.ts` deben ser relativas a `/api`, por ejemplo:

```ts
apiClient.get("/auth/me")
apiClient.get("/logistics/arrival-notices")
```

No concatenar `/api` dos veces.

## Resultado de la auditoría

- Operaciones declaradas por el inventario frontend: 215.
- Operaciones que existen en Cloud Run: 73.
- Operaciones inexistentes: 142.
- OpenAPI publicado: versión `0.9.3`, 639 operaciones.
- Backend local: 639 operaciones.
- Diferencia entre Cloud Run y local: 0 operaciones.
- Revisión activa: `autenticacion-continua-api-v0-9-3`, con 100 % del tráfico.
- Las 155 operaciones de portón, muelles, asignaciones y descarga que faltaban ya están desplegadas.

## Rutas base válidas del inventario

```text
GET    /auth/me
POST   /auth/login
POST   /auth/logout
POST   /auth/logout-all
POST   /auth/register
POST   /auth/change-password
GET    /auth/sessions
DELETE /auth/sessions/{session_id}

GET    /continuous-auth/status
POST   /continuous-auth/evaluate
POST   /continuous-auth/reverify
GET    /i18n/catalog
GET    /health

GET    /research/consent/current
POST   /research/consent
POST   /research/consent/withdraw
GET    /research/participants?page_size=100
GET    /research/participants/me
POST   /research/participants/self-enroll
GET    /research/sessions?page_size=100
POST   /research/sessions/start
GET    /models/status

GET    /logistics/me
POST   /logistics/me/context
GET    /logistics/me/permissions
POST   /logistics/authorization/check
```

## Avisos de llegada

Estas son las rutas inbound que sí están desplegadas y deben utilizarse antes de cualquier operación física:

```text
GET    /logistics/arrival-notices
POST   /logistics/arrival-notices
GET    /logistics/arrival-notices/{arrival_notice_id}
PATCH  /logistics/arrival-notices/{arrival_notice_id}
POST   /logistics/arrival-notices/{arrival_notice_id}/validate
POST   /logistics/arrival-notices/{arrival_notice_id}/submit
POST   /logistics/arrival-notices/{arrival_notice_id}/mark-under-review
POST   /logistics/arrival-notices/{arrival_notice_id}/request-changes
POST   /logistics/arrival-notices/{arrival_notice_id}/mark-ready
POST   /logistics/arrival-notices/{arrival_notice_id}/cancel
POST   /logistics/arrival-notices/{arrival_notice_id}/copy
GET    /logistics/arrival-notices/{arrival_notice_id}/history
GET    /logistics/arrival-notices/{arrival_notice_id}/capabilities
GET    /logistics/arrival-notices/{arrival_notice_id}/files
GET    /logistics/arrival-notices/{arrival_notice_id}/source-orders
GET    /logistics/arrival-notices/{arrival_notice_id}/transport-readiness
GET    /logistics/arrival-notices/{arrival_notice_id}/revisions
POST   /logistics/arrival-notices/{arrival_notice_id}/revisions

GET    /logistics/arrival-notice-revisions/{revision_id}
GET    /logistics/arrival-notice-revisions/{revision_id}/lines
POST   /logistics/arrival-notice-revisions/{revision_id}/lines
PUT    /logistics/arrival-notice-revisions/{revision_id}/vehicle-reference
PUT    /logistics/arrival-notice-revisions/{revision_id}/driver-reference
GET    /logistics/arrival-notice-revisions/{revision_id}/transport-documents
POST   /logistics/arrival-notice-revisions/{revision_id}/transport-documents

PATCH  /logistics/arrival-notice-lines/{line_id}
POST   /logistics/arrival-notice-lines/{line_id}/cancel
POST   /logistics/arrival-notice-lines/reorder
POST   /logistics/arrival-notice-lines/validate

PATCH  /logistics/arrival-transport-documents/{document_id}
POST   /logistics/arrival-transport-documents/{document_id}/archive
POST   /logistics/arrival-transport-documents/{document_id}/associate-file
POST   /logistics/arrival-transport-documents/{document_id}/verify-format
```

## Calendarios y citas de recepción

```text
GET    /logistics/reception-calendars
POST   /logistics/reception-calendars
GET    /logistics/reception-calendars/{calendar_id}
PATCH  /logistics/reception-calendars/{calendar_id}
POST   /logistics/reception-calendars/{calendar_id}/activate
POST   /logistics/reception-calendars/{calendar_id}/deactivate
POST   /logistics/reception-calendars/{calendar_id}/archive
GET    /logistics/reception-calendars/{calendar_id}/operating-windows
POST   /logistics/reception-calendars/{calendar_id}/operating-windows
GET    /logistics/reception-calendars/{calendar_id}/blackouts
POST   /logistics/reception-calendars/{calendar_id}/blackouts
POST   /logistics/reception-calendars/{calendar_id}/availability

POST   /logistics/reception-appointment-holds
GET    /logistics/reception-appointment-holds/{hold_id}
POST   /logistics/reception-appointment-holds/{hold_id}/cancel
POST   /logistics/reception-appointment-holds/{hold_id}/refresh

GET    /logistics/reception-appointments
POST   /logistics/reception-appointments
GET    /logistics/reception-appointments/{appointment_id}
POST   /logistics/reception-appointments/{appointment_id}/validate
POST   /logistics/reception-appointments/{appointment_id}/confirm
POST   /logistics/reception-appointments/{appointment_id}/request-reschedule
POST   /logistics/reception-appointments/{appointment_id}/reschedule
POST   /logistics/reception-appointments/{appointment_id}/cancel
GET    /logistics/reception-appointments/{appointment_id}/history
GET    /logistics/reception-appointments/{appointment_id}/capabilities
GET    /logistics/reception-appointments/{appointment_id}/gate-preparation
GET    /logistics/reception-appointments/{appointment_id}/preview
POST   /logistics/reception-appointments/{appointment_id}/issue
GET    /logistics/reception-appointments/{appointment_id}/document
POST   /logistics/reception-appointments/{appointment_id}/package

GET    /logistics/reception-appointment-packages/{package_id}
GET    /logistics/reception-appointment-packages/{package_id}/download
```

## Órdenes de compra

La base correcta es `/logistics/procurement/purchase-orders`. No usar `/logistics/purchasing/purchase-orders`.

```text
POST   /logistics/procurement/purchase-orders/plan-generation
GET    /logistics/procurement/purchase-orders
GET    /logistics/procurement/purchase-orders/{po_id}
POST   /logistics/procurement/purchase-orders/{po_id}/submit
POST   /logistics/procurement/purchase-orders/{po_id}/approve
POST   /logistics/procurement/purchase-orders/{po_id}/reject
POST   /logistics/procurement/purchase-orders/{po_id}/return-for-changes
POST   /logistics/procurement/purchase-orders/{po_id}/cancel
```

El backend publicado no expone el CRUD de líneas, archivos, acknowledgements, amendments, dispatch o schedules declarado por el inventario.

## Aprobaciones de compras

```text
POST   /logistics/procurement-approvals/policies
GET    /logistics/procurement-approvals/policies
GET    /logistics/procurement-approvals/policies/{policy_id}
POST   /logistics/procurement-approvals/policy-versions/{version_id}/conditions
POST   /logistics/procurement-approvals/policy-versions/{version_id}/steps
POST   /logistics/procurement-approvals/policy-versions/{version_id}/activate
POST   /logistics/procurement-approvals/requests
GET    /logistics/procurement-approvals/requests/{request_id}
GET    /logistics/procurement-approvals/assignments/my-pending
POST   /logistics/procurement-approvals/assignments/{assignment_id}/decision
GET    /logistics/procurement-approvals/requests/{request_id}/audit-seal
```

No existen los endpoints raíz `GET /procurement-approvals` ni las acciones `/approve`, `/reject` o `/history` declaradas por el inventario.

## Evaluaciones de proveedores

La base correcta es `/logistics/supplier-evaluations`.

```text
GET    /logistics/supplier-evaluations/templates
POST   /logistics/supplier-evaluations/templates
POST   /logistics/supplier-evaluations/templates/{template_id}/versions
POST   /logistics/supplier-evaluations/versions/{version_id}/activate
POST   /logistics/supplier-evaluations/evaluations
POST   /logistics/supplier-evaluations/evaluations/{evaluation_id}/calculate
POST   /logistics/supplier-evaluations/evaluations/{evaluation_id}/manual-scores
POST   /logistics/supplier-evaluations/evaluations/{evaluation_id}/decisions
```

## Vehículos

No existe `GET /logistics/vehicles` ni `PATCH /logistics/vehicles/{vehicle_id}` en el contrato publicado.

```text
POST   /logistics/vehicles
GET    /logistics/vehicles/{vehicle_id}
POST   /logistics/vehicles/{vehicle_id}/activate
POST   /logistics/vehicles/{vehicle_id}/block
POST   /logistics/vehicles/{vehicle_id}/unblock
POST   /logistics/vehicles/{vehicle_id}/plate-change
POST   /logistics/vehicles/{vehicle_id}/capacity-profiles
POST   /logistics/vehicles/{vehicle_id}/owner-assignments
POST   /logistics/vehicles/{vehicle_id}/carrier-assignments
POST   /logistics/vehicles/{vehicle_id}/documents
GET    /logistics/vehicles/{vehicle_id}/documents
POST   /logistics/vehicles/{vehicle_id}/verifications
GET    /logistics/vehicles/{vehicle_id}/verifications
GET    /logistics/vehicles/{vehicle_id}/verification-compliance
POST   /logistics/vehicles/{vehicle_id}/assisted-verifications

GET    /logistics/vehicle-makes
POST   /logistics/vehicle-makes
GET    /logistics/vehicle-makes/{make_id}/models
POST   /logistics/vehicle-models
GET    /logistics/vehicle-verification-sources
POST   /logistics/vehicle-verifications/{verification_id}/apply
POST   /logistics/assisted-vehicle-verifications/{assisted_id}/approve
```

## Costos, unidades y archivos

```text
GET    /logistics/cost-centers
POST   /logistics/cost-centers
GET    /logistics/cost-centers/{cost_center_id}
PATCH  /logistics/cost-centers/{cost_center_id}
POST   /logistics/cost-centers/{cost_center_id}/activate
POST   /logistics/cost-centers/{cost_center_id}/deactivate
POST   /logistics/cost-centers/{cost_center_id}/archive

POST   /logistics/unit-conversion-rules
POST   /logistics/unit-conversions/evaluate
POST   /logistics/unit-conversions/compare

POST   /logistics/files/upload-sessions
POST   /logistics/files/upload-sessions/{session_id}/finalize
GET    /logistics/files
GET    /logistics/files/{file_id}
PATCH  /logistics/files/{file_id}
GET    /logistics/files/{file_id}/versions
GET    /logistics/files/{file_id}/download
GET    /logistics/files/{file_id}/preview
POST   /logistics/files/{file_id}/archive
POST   /logistics/files/{file_id}/restore
POST   /logistics/files/{file_id}/associations
```

No usar `GET /logistics/catalog/cost-centers`, `GET /logistics/unit-conversion-rules`, `GET /logistics/document-exports` ni `POST /logistics/files`.

## Rutas físicas desplegadas en Cloud Run

Las siguientes bases del inventario original continúan siendo incorrectas, aunque la funcionalidad ya está desplegada con otros nombres:

```text
/logistics/inbound/dock-queue
/logistics/inbound/docks
/logistics/inbound/dock-assignment-plans
/logistics/inbound/dock-assignments
/logistics/inbound/unloading
/logistics/inbound/dock-metrics
/logistics/inbound/gate-control
/logistics/evidence
```

Las bases correctas publicadas en Cloud Run `0.9.3` son:

```text
/logistics/warehouse-gates
/logistics/gate-check-ins
/logistics/inbound-dock-queue
/logistics/warehouse-docks
/logistics/dock-assignment-plans
/logistics/inbound-dock-assignments
/logistics/unloading-operations
/logistics/dock-operation-metrics
/logistics/dock-operation-exports
/logistics/files/evidence
```

Ya pueden habilitarse en el frontend, siempre usando estas bases correctas y los métodos definidos por el OpenAPI publicado. No conservar aliases con `/logistics/inbound/docks`, `/logistics/inbound/unloading` o `/logistics/inbound/gate-control`, porque esas rutas siguen sin existir.

## Rutas legacy

Las rutas legacy declaradas siguen publicadas, excepto esta discrepancia:

```text
INCORRECTA PATCH /shipments/{shipment_id}/status
CORRECTA   POST  /shipments/{shipment_id}/status
```

También existe `PATCH /shipments/{shipment_id}` para actualizar el envío.

## Fuente de verdad

Antes de compilar el frontend, validar siempre contra:

```text
https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/openapi.json
```

Las rutas locales que no aparezcan en ese documento deben permanecer detrás de una feature flag o fuera de la navegación productiva.
