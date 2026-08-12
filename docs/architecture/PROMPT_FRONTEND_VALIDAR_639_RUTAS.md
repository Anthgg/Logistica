# Prompt para validar todas las rutas del frontend

Copiar desde `INICIO DEL PROMPT` hasta `FIN DEL PROMPT` y pegarlo en la tarea del frontend.

## INICIO DEL PROMPT

Actúa como arquitecto frontend senior especializado en React, Vite y TypeScript estricto.

Trabaja únicamente en el frontend ubicado normalmente en:

`C:\Users\anthg\OneDrive\Escritorio\proyecto tesis front\frontend`

Si esa ruta no es el checkout activo, localiza primero el proyecto React/Vite real. No modifiques el backend, sus migraciones, Docker, Cloud Run ni la base de datos.

### Objetivo

Audita exhaustivamente todas las llamadas API del frontend y alinea sus clientes, hooks, servicios, pruebas y validadores con el contrato desplegado de Cloud Run.

Contrato verificado:

- Servicio: `autenticacion-continua-api`.
- Versión OpenAPI: `0.9.3`.
- Operaciones HTTP: `639`.
- OpenAPI oficial: `https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/openapi.json`.
- Base URL de negocio: `https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api`.

Las rutas del inventario incluido al final son paths completos tal como aparecen en OpenAPI. Casi todas las rutas de negocio comienzan por `/api`. Si `api-client.ts` configura una base terminada en `/api`, sus llamadas internas deben ser relativas, por ejemplo `/auth/me` y `/logistics/arrival-notices`. Nunca construyas `/api/api/...`. Las sondas raíz `GET /health`, `GET /live` y `GET /ready` son la excepción: no llevan `/api` y deben consultarse contra el origen del servicio.

### Reglas obligatorias

1. Usa el OpenAPI oficial como fuente de verdad. La lista incluida abajo es un snapshot completo para facilitar la auditoría, pero vuelve a consultar `/openapi.json` si está accesible.
2. No inventes rutas, aliases, métodos HTTP, parámetros, DTOs ni fallbacks que oculten errores.
3. Normaliza los nombres de parámetros de ruta al comparar: `{id}`, `{vehicleId}` y `{vehicle_id}` representan estructuralmente un parámetro, pero el cliente debe usar nombres TypeScript coherentes.
4. Ignora el query string al validar la existencia del path; valida los query parameters contra OpenAPI por separado.
5. Todas las requests autenticadas deben usar `credentials: "include"`.
6. Las operaciones mutables deben utilizar el mecanismo CSRF existente y enviar `X-CSRF-Token`; no guardar el token en `localStorage`.
7. Conserva `Idempotency-Key`, `If-Match`, `X-Correlation-ID` y step-up cuando el contrato o el cliente existente lo requieran.
8. Un `401` o `403` demuestra que una ruta protegida existe; no lo clasifiques como `404`.
9. No uses los nombres obsoletos `/logistics/inbound/docks`, `/logistics/inbound/unloading` o `/logistics/inbound/gate-control`. Las bases correctas son `/logistics/warehouse-docks`, `/logistics/unloading-operations`, `/logistics/gate-check-ins` y `/logistics/warehouse-gates`.
10. La base correcta de órdenes es `/logistics/procurement/purchase-orders`, no `/logistics/purchasing/purchase-orders`.
11. Las evaluaciones usan `/logistics/supplier-evaluations`.
12. Los archivos se cargan con `/logistics/files/upload-sessions` y luego `/finalize`; no existe `POST /logistics/files` como carga directa.
13. No existe `GET /logistics/vehicles`; no hagas esa llamada ni simules que devuelve datos. Usa únicamente las operaciones publicadas.
14. No elimines clientes legacy solo porque exista un módulo logístico equivalente. Primero identifica páginas, menús, hooks, pruebas y consumidores activos.
15. No cambies rutas de navegación React como si fueran endpoints API. Audita por separado rutas UI y rutas HTTP.

### Procedimiento

1. Inspecciona `package.json`, configuración Vite, TypeScript, router, `src/api`, hooks, stores, páginas, componentes y pruebas.
2. Localiza todas las llamadas realizadas mediante `fetch`, Axios, `apiClient`, React Query, mutaciones, loaders, servicios y URLs construidas dinámicamente.
3. Extrae una matriz con estas columnas: archivo, línea, método, ruta frontend, operación OpenAPI encontrada, estado y acción.
4. Clasifica cada llamada como `VALIDA`, `METODO_INCORRECTO`, `RUTA_INCORRECTA`, `PARAMETROS_INCORRECTOS`, `DTO_INCOMPATIBLE`, `NO_PUBLICADA` o `LEGACY_EN_USO`.
5. Detecta llamadas duplicadas, bases `/api` duplicadas, diferencias singular/plural, prefijos antiguos y acciones inexistentes.
6. Revisa también `scripts/validate-openapi.mjs` o su equivalente. Haz que valide automáticamente todas las rutas realmente consumidas por el frontend.
7. Antes de editar, presenta el inventario de discrepancias. Después corrige únicamente el frontend.
8. Actualiza tipos y DTOs desde OpenAPI o desde los esquemas actuales; no uses `any` para silenciar incompatibilidades.
9. Añade o actualiza pruebas para cada cliente corregido, incluyendo método, URL, payload, query params y manejo de `401`, `403`, `404`, `409`, `422` y `5xx` cuando aplique.
10. Ejecuta TypeScript estricto, pruebas enfocadas, suite completa, validador OpenAPI, lint y build de Vite.
11. No declares éxito si existe alguna llamada frontend que no corresponda a una operación del contrato.

### Entregable final obligatorio

Reporta:

- Total de llamadas API encontradas en el frontend.
- Total válidas antes y después.
- Rutas corregidas, con archivo y línea.
- Rutas eliminadas o deshabilitadas y motivo.
- Rutas backend publicadas sin consumidor frontend.
- Errores de DTO o parámetros corregidos.
- Resultado de TypeScript, pruebas, OpenAPI, lint y build.
- Archivos creados y modificados.
- Riesgos pendientes.
- Confirmación explícita de que no modificaste backend, Docker, Cloud Run ni base de datos.

### Contrato HTTP completo desplegado

```text
DELETE /api/auth/sessions/{session_id}
DELETE /api/clients/{client_id}
DELETE /api/logistics/procurement/requisitions/{requisition_id}/lines/{line_id}
DELETE /api/routes/{route_id}/shipments/{shipment_id}
DELETE /api/warehouses/{warehouse_id}
GET    /api/auth/csrf
GET    /api/auth/me
GET    /api/auth/sessions
GET    /api/clients
GET    /api/clients/{client_id}
GET    /api/continuous-auth/evaluations
GET    /api/continuous-auth/evaluations/{evaluation_id}
GET    /api/continuous-auth/status
GET    /api/dashboard/summary
GET    /api/health
GET    /api/i18n/catalog
GET    /api/incidents
GET    /api/incidents/{incident_id}
GET    /api/inventory
GET    /api/inventory/movements
GET    /api/inventory/{item_id}
GET    /api/logistics/arrival-notice-revisions/{revision_id}
GET    /api/logistics/arrival-notice-revisions/{revision_id}/lines
GET    /api/logistics/arrival-notice-revisions/{revision_id}/transport-documents
GET    /api/logistics/arrival-notices
GET    /api/logistics/arrival-notices/{arrival_notice_id}
GET    /api/logistics/arrival-notices/{arrival_notice_id}/capabilities
GET    /api/logistics/arrival-notices/{arrival_notice_id}/files
GET    /api/logistics/arrival-notices/{arrival_notice_id}/history
GET    /api/logistics/arrival-notices/{arrival_notice_id}/revisions
GET    /api/logistics/arrival-notices/{arrival_notice_id}/source-orders
GET    /api/logistics/arrival-notices/{arrival_notice_id}/transport-readiness
GET    /api/logistics/audit-events
GET    /api/logistics/audit-events/by-correlation/{correlation_id}
GET    /api/logistics/audit-events/by-resource/{resource_type}/{resource_id}
GET    /api/logistics/audit-events/{event_id}
GET    /api/logistics/branches/{branch_id}
GET    /api/logistics/branches/{branch_id}/warehouses
GET    /api/logistics/business-partners
GET    /api/logistics/business-partners/{partner_id}
GET    /api/logistics/company-profile
GET    /api/logistics/company-profile/addresses
GET    /api/logistics/company-profile/assets
GET    /api/logistics/company-profile/assets/{asset_id}/content
GET    /api/logistics/company-profile/contacts
GET    /api/logistics/company-profile/numbering-policies
GET    /api/logistics/company-profile/signers
GET    /api/logistics/company-profile/versions
GET    /api/logistics/cost-centers
GET    /api/logistics/cost-centers/{cost_center_id}
GET    /api/logistics/dock-operation-exports/{export_job_id}
GET    /api/logistics/dock-operation-exports/{export_job_id}/download
GET    /api/logistics/dock-operation-metrics
GET    /api/logistics/document-catalog
GET    /api/logistics/document-catalog/families
GET    /api/logistics/document-catalog/families/{family_code}
GET    /api/logistics/document-catalog/retention-policies
GET    /api/logistics/document-catalog/types
GET    /api/logistics/document-catalog/types/{document_type_code}
GET    /api/logistics/document-catalog/types/{document_type_code}/active-version
GET    /api/logistics/document-catalog/types/{document_type_code}/versions
GET    /api/logistics/document-catalog/version
GET    /api/logistics/document-code-standard
GET    /api/logistics/document-code-standard/examples
GET    /api/logistics/document-code-standard/versions
GET    /api/logistics/document-packages/{operation_id}.zip
GET    /api/logistics/document-packages/{operation_type}/{operation_id}.zip
GET    /api/logistics/document-renderer/status
GET    /api/logistics/document-series
GET    /api/logistics/document-series/{series_id}
GET    /api/logistics/document-series/{series_id}/numbers
GET    /api/logistics/document-series/{series_id}/talonario.pdf
GET    /api/logistics/document-series/{series_id}/talonarios
GET    /api/logistics/document-site-codes
GET    /api/logistics/document-talonarios/{talonario_id}
GET    /api/logistics/document-talonarios/{talonario_id}/manifest
GET    /api/logistics/document-talonarios/{talonario_id}/numbers
GET    /api/logistics/document-talonarios/{talonario_id}/pdf
GET    /api/logistics/document-templates
GET    /api/logistics/document-templates/{template_key}
GET    /api/logistics/document-templates/{template_key}/versions
GET    /api/logistics/documents
GET    /api/logistics/documents/{document_id}
GET    /api/logistics/documents/{document_id}/history
GET    /api/logistics/documents/{document_id}/pdf
GET    /api/logistics/documents/{document_id}/preview
GET    /api/logistics/driver-license-categories
GET    /api/logistics/drivers
GET    /api/logistics/drivers/{driver_id}
GET    /api/logistics/drivers/{driver_id}/alerts
GET    /api/logistics/files
GET    /api/logistics/files/evidence/{evidence_id}/custody-events
GET    /api/logistics/files/{file_id}
GET    /api/logistics/files/{file_id}/download
GET    /api/logistics/files/{file_id}/preview
GET    /api/logistics/files/{file_id}/versions
GET    /api/logistics/gate-check-ins
GET    /api/logistics/gate-check-ins/{check_in_id}
GET    /api/logistics/gate-check-ins/{check_in_id}/capabilities
GET    /api/logistics/gate-check-ins/{check_in_id}/check-results
GET    /api/logistics/gate-check-ins/{check_in_id}/corrections
GET    /api/logistics/gate-check-ins/{check_in_id}/dock-preparation
GET    /api/logistics/gate-check-ins/{check_in_id}/document
GET    /api/logistics/gate-check-ins/{check_in_id}/documents
GET    /api/logistics/gate-check-ins/{check_in_id}/driver-inspection
GET    /api/logistics/gate-check-ins/{check_in_id}/exceptions
GET    /api/logistics/gate-check-ins/{check_in_id}/history
GET    /api/logistics/gate-check-ins/{check_in_id}/integrity
GET    /api/logistics/gate-check-ins/{check_in_id}/photos
GET    /api/logistics/gate-check-ins/{check_in_id}/preview
GET    /api/logistics/gate-check-ins/{check_in_id}/seal-inspection
GET    /api/logistics/gate-check-ins/{check_in_id}/vehicle-inspection
GET    /api/logistics/health
GET    /api/logistics/inbound-dock-assignments
GET    /api/logistics/inbound-dock-assignments/{assignment_id}
GET    /api/logistics/inbound-dock-assignments/{assignment_id}/capabilities
GET    /api/logistics/inbound-dock-assignments/{assignment_id}/history
GET    /api/logistics/inbound-dock-assignments/{assignment_id}/metrics
GET    /api/logistics/inbound-dock-queue
GET    /api/logistics/inbound-dock-queue/ordered
GET    /api/logistics/inbound-dock-queue/summary
GET    /api/logistics/inbound-dock-queue/{queue_entry_id}
GET    /api/logistics/inbound-dock-queue/{queue_entry_id}/history
GET    /api/logistics/integrations/
GET    /api/logistics/me
GET    /api/logistics/me/permissions
GET    /api/logistics/me/roles
GET    /api/logistics/measurement-dimensions
GET    /api/logistics/organizations
GET    /api/logistics/organizations/{organization_id}
GET    /api/logistics/organizations/{organization_id}/branches
GET    /api/logistics/permissions
GET    /api/logistics/permissions/{permission_id}
GET    /api/logistics/procurement-approvals/assignments/my-pending
GET    /api/logistics/procurement-approvals/policies
GET    /api/logistics/procurement-approvals/policies/{policy_id}
GET    /api/logistics/procurement-approvals/requests/{request_id}
GET    /api/logistics/procurement-approvals/requests/{request_id}/audit-seal
GET    /api/logistics/procurement/purchase-orders
GET    /api/logistics/procurement/purchase-orders/{po_id}
GET    /api/logistics/procurement/requisitions
GET    /api/logistics/procurement/requisitions/{requisition_id}
GET    /api/logistics/procurement/requisitions/{requisition_id}/capabilities
GET    /api/logistics/procurement/requisitions/{requisition_id}/comments
GET    /api/logistics/procurement/requisitions/{requisition_id}/document/preview
GET    /api/logistics/procurement/requisitions/{requisition_id}/history
GET    /api/logistics/procurement/requisitions/{requisition_id}/lines
GET    /api/logistics/procurement/requisitions/{requisition_id}/revisions
GET    /api/logistics/product-brands
GET    /api/logistics/product-categories
GET    /api/logistics/product-categories/tree
GET    /api/logistics/products
GET    /api/logistics/products/identifiers/{identifier_id}/barcode
GET    /api/logistics/products/{product_id}
GET    /api/logistics/products/{product_id}/unit-configuration
GET    /api/logistics/products/{product_id}/versions
GET    /api/logistics/reception-appointment-holds/{hold_id}
GET    /api/logistics/reception-appointment-packages/{package_id}
GET    /api/logistics/reception-appointment-packages/{package_id}/download
GET    /api/logistics/reception-appointments
GET    /api/logistics/reception-appointments/{appointment_id}
GET    /api/logistics/reception-appointments/{appointment_id}/capabilities
GET    /api/logistics/reception-appointments/{appointment_id}/document
GET    /api/logistics/reception-appointments/{appointment_id}/gate-preparation
GET    /api/logistics/reception-appointments/{appointment_id}/history
GET    /api/logistics/reception-appointments/{appointment_id}/preview
GET    /api/logistics/reception-calendars
GET    /api/logistics/reception-calendars/{calendar_id}
GET    /api/logistics/reception-calendars/{calendar_id}/blackouts
GET    /api/logistics/reception-calendars/{calendar_id}/operating-windows
GET    /api/logistics/role-assignments/{assignment_id}
GET    /api/logistics/roles
GET    /api/logistics/roles/{role_id}
GET    /api/logistics/roles/{role_id}/permissions
GET    /api/logistics/roles/{role_id}/scope-rules
GET    /api/logistics/routes/
GET    /api/logistics/ruc/datasets/current
GET    /api/logistics/ruc/imports/{job_id}
GET    /api/logistics/ruc/sources/health
GET    /api/logistics/ruc/{ruc}
GET    /api/logistics/security/policies
GET    /api/logistics/security/step-up/challenges/{challenge_id}
GET    /api/logistics/supplier-evaluations/templates
GET    /api/logistics/units
GET    /api/logistics/unloading-operations
GET    /api/logistics/unloading-operations/{operation_id}
GET    /api/logistics/unloading-operations/{operation_id}/capabilities
GET    /api/logistics/unloading-operations/{operation_id}/completion-checks
GET    /api/logistics/unloading-operations/{operation_id}/equipment
GET    /api/logistics/unloading-operations/{operation_id}/history
GET    /api/logistics/unloading-operations/{operation_id}/integrity
GET    /api/logistics/unloading-operations/{operation_id}/metrics
GET    /api/logistics/unloading-operations/{operation_id}/operational-times
GET    /api/logistics/unloading-operations/{operation_id}/pauses
GET    /api/logistics/unloading-operations/{operation_id}/readiness-checks
GET    /api/logistics/unloading-operations/{operation_id}/receiving-preparation
GET    /api/logistics/unloading-operations/{operation_id}/responsibles
GET    /api/logistics/unloading-operations/{operation_id}/seal-opening
GET    /api/logistics/unloading-operations/{operation_id}/time-corrections
GET    /api/logistics/unloading-pauses/{pause_id}
GET    /api/logistics/users/{user_id}/role-assignments
GET    /api/logistics/vehicle-makes
GET    /api/logistics/vehicle-makes/{make_id}/models
GET    /api/logistics/vehicle-verification-sources
GET    /api/logistics/vehicles/{vehicle_id}
GET    /api/logistics/vehicles/{vehicle_id}/documents
GET    /api/logistics/vehicles/{vehicle_id}/verification-compliance
GET    /api/logistics/vehicles/{vehicle_id}/verifications
GET    /api/logistics/warehouse-docks
GET    /api/logistics/warehouse-docks/{dock_id}
GET    /api/logistics/warehouse-docks/{dock_id}/availability
GET    /api/logistics/warehouse-docks/{dock_id}/blackouts
GET    /api/logistics/warehouse-docks/{dock_id}/capabilities
GET    /api/logistics/warehouse-docks/{dock_id}/history
GET    /api/logistics/warehouse-docks/{dock_id}/operating-windows
GET    /api/logistics/warehouse-docks/{dock_id}/operational-status
GET    /api/logistics/warehouse-docks/{dock_id}/schedule
GET    /api/logistics/warehouse-gates
GET    /api/logistics/warehouse-gates/{gate_id}
GET    /api/logistics/warehouse-gates/{gate_id}/current-queue
GET    /api/logistics/warehouse-gates/{gate_id}/today-summary
GET    /api/logistics/warehouses
GET    /api/logistics/warehouses/location-qr/{public_reference}
GET    /api/logistics/warehouses/locations/{location_id}
GET    /api/logistics/warehouses/locations/{location_id}/capacities
GET    /api/logistics/warehouses/locations/{location_id}/label.pdf
GET    /api/logistics/warehouses/locations/{location_id}/qr
GET    /api/logistics/warehouses/locations/{location_id}/restrictions
GET    /api/logistics/warehouses/{warehouse_id}
GET    /api/logistics/warehouses/{warehouse_id}/location-tree
GET    /api/logistics/warehouses/{warehouse_id}/locations
GET    /api/logistics/warehouses/{warehouse_id}/logical-map
GET    /api/models/status
GET    /api/reports/deliveries-by-date
GET    /api/reports/incidents-summary
GET    /api/reports/low-stock
GET    /api/reports/routes-summary
GET    /api/reports/shipments-by-priority
GET    /api/reports/shipments-by-status
GET    /api/research/consent/current
GET    /api/research/participants
GET    /api/research/participants/me
GET    /api/research/participants/{participant_id}
GET    /api/research/sessions
GET    /api/research/sessions/{session_id}
GET    /api/routes
GET    /api/routes/{route_id}
GET    /api/shipments
GET    /api/shipments/{shipment_id}
GET    /api/shipments/{shipment_id}/timeline
GET    /api/warehouses
GET    /api/warehouses/{warehouse_id}
GET    /health
GET    /live
GET    /ready
PATCH  /api/clients/{client_id}
PATCH  /api/incidents/{incident_id}
PATCH  /api/inventory/{item_id}
PATCH  /api/logistics/arrival-notice-lines/{line_id}
PATCH  /api/logistics/arrival-notices/{arrival_notice_id}
PATCH  /api/logistics/arrival-transport-documents/{document_id}
PATCH  /api/logistics/branches/{branch_id}
PATCH  /api/logistics/branches/{branch_id}/status
PATCH  /api/logistics/company-profile
PATCH  /api/logistics/company-profile/addresses/{address_id}
PATCH  /api/logistics/company-profile/contacts/{contact_id}
PATCH  /api/logistics/company-profile/signers/{signer_id}
PATCH  /api/logistics/cost-centers/{cost_center_id}
PATCH  /api/logistics/drivers/{driver_id}
PATCH  /api/logistics/files/{file_id}
PATCH  /api/logistics/organizations/{organization_id}
PATCH  /api/logistics/organizations/{organization_id}/status
PATCH  /api/logistics/procurement/requisitions/{requisition_id}
PATCH  /api/logistics/procurement/requisitions/{requisition_id}/lines/{line_id}
PATCH  /api/logistics/reception-calendars/{calendar_id}
PATCH  /api/logistics/role-assignments/{assignment_id}/dates
PATCH  /api/logistics/warehouse-dock-operating-windows/{window_id}
PATCH  /api/logistics/warehouse-docks/{dock_id}
PATCH  /api/logistics/warehouse-gates/{gate_id}
PATCH  /api/logistics/warehouses/{warehouse_id}/status
PATCH  /api/research/participants/{participant_id}
PATCH  /api/research/sessions/{session_id}/annotation
PATCH  /api/routes/{route_id}
PATCH  /api/shipments/{shipment_id}
PATCH  /api/warehouses/{warehouse_id}
POST   /api/auth/change-password
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/logout-all
POST   /api/auth/refresh
POST   /api/auth/register
POST   /api/clients
POST   /api/continuous-auth/evaluate
POST   /api/continuous-auth/reverify
POST   /api/incidents
POST   /api/incidents/{incident_id}/resolve
POST   /api/inventory
POST   /api/inventory/movements
POST   /api/logistics/arrival-notice-lines/reorder
POST   /api/logistics/arrival-notice-lines/validate
POST   /api/logistics/arrival-notice-lines/{line_id}/cancel
POST   /api/logistics/arrival-notice-revisions/{revision_id}/lines
POST   /api/logistics/arrival-notice-revisions/{revision_id}/transport-documents
POST   /api/logistics/arrival-notices
POST   /api/logistics/arrival-notices/{arrival_notice_id}/cancel
POST   /api/logistics/arrival-notices/{arrival_notice_id}/copy
POST   /api/logistics/arrival-notices/{arrival_notice_id}/mark-ready
POST   /api/logistics/arrival-notices/{arrival_notice_id}/mark-under-review
POST   /api/logistics/arrival-notices/{arrival_notice_id}/request-changes
POST   /api/logistics/arrival-notices/{arrival_notice_id}/revisions
POST   /api/logistics/arrival-notices/{arrival_notice_id}/submit
POST   /api/logistics/arrival-notices/{arrival_notice_id}/validate
POST   /api/logistics/arrival-transport-documents/{document_id}/archive
POST   /api/logistics/arrival-transport-documents/{document_id}/associate-file
POST   /api/logistics/arrival-transport-documents/{document_id}/verify-format
POST   /api/logistics/assisted-vehicle-verifications/{assisted_id}/approve
POST   /api/logistics/audit-events/{event_id}/verify-integrity
POST   /api/logistics/authorization/check
POST   /api/logistics/branches/{branch_id}/warehouses
POST   /api/logistics/business-partners
POST   /api/logistics/business-partners/duplicate-check
POST   /api/logistics/business-partners/{partner_id}/activate
POST   /api/logistics/business-partners/{partner_id}/addresses
POST   /api/logistics/business-partners/{partner_id}/block
POST   /api/logistics/business-partners/{partner_id}/contacts
POST   /api/logistics/business-partners/{partner_id}/evaluations
POST   /api/logistics/business-partners/{partner_id}/roles
POST   /api/logistics/company-profile
POST   /api/logistics/company-profile/addresses
POST   /api/logistics/company-profile/addresses/{address_id}/set-primary
POST   /api/logistics/company-profile/assets/logo
POST   /api/logistics/company-profile/assets/{asset_id}/activate
POST   /api/logistics/company-profile/assets/{asset_id}/revoke
POST   /api/logistics/company-profile/contacts
POST   /api/logistics/company-profile/contacts/{contact_id}/set-primary
POST   /api/logistics/company-profile/document-preview
POST   /api/logistics/company-profile/numbering-policies
POST   /api/logistics/company-profile/numbering-policies/preview
POST   /api/logistics/company-profile/signers
POST   /api/logistics/company-profile/signers/{signer_id}/activate
POST   /api/logistics/company-profile/signers/{signer_id}/revoke
POST   /api/logistics/company-profile/signers/{signer_id}/signature
POST   /api/logistics/company-profile/signers/{signer_id}/suspend
POST   /api/logistics/company-profile/versions
POST   /api/logistics/company-profile/versions/{version_id}/activate
POST   /api/logistics/cost-centers
POST   /api/logistics/cost-centers/{cost_center_id}/activate
POST   /api/logistics/cost-centers/{cost_center_id}/archive
POST   /api/logistics/cost-centers/{cost_center_id}/deactivate
POST   /api/logistics/delivery/documents/{document_type_code}/pdf
POST   /api/logistics/delivery/documents/{document_type_code}/preview
POST   /api/logistics/dispatch/document-package/manifest
POST   /api/logistics/dispatch/documents/{document_type_code}/pdf
POST   /api/logistics/dispatch/documents/{document_type_code}/preview
POST   /api/logistics/dock-assignment-plans
POST   /api/logistics/dock-assignment-plans/{assignment_hash}/execute
POST   /api/logistics/dock-operation-expodrts
POST   /api/logistics/dock-operational-time-corrections/{correction_id}/approve
POST   /api/logistics/dock-operational-time-corrections/{correction_id}/reject
POST   /api/logistics/document-catalog/validate
POST   /api/logistics/document-code-standard/parse
POST   /api/logistics/document-code-standard/preview
POST   /api/logistics/document-code-standard/validate
POST   /api/logistics/document-series
POST   /api/logistics/document-series/{series_id}/activate
POST   /api/logistics/document-series/{series_id}/close
POST   /api/logistics/document-series/{series_id}/suspend
POST   /api/logistics/document-series/{series_id}/talonarios
POST   /api/logistics/document-talonarios/{talonario_id}/cancel
POST   /api/logistics/document-talonarios/{talonario_id}/exports
POST   /api/logistics/document-templates/{template_key}/preview
POST   /api/logistics/documents
POST   /api/logistics/documents/export
POST   /api/logistics/documents/{document_id}/cancel
POST   /api/logistics/documents/{document_id}/issue
POST   /api/logistics/documents/{document_id}/print-events
POST   /api/logistics/documents/{document_id}/reprint
POST   /api/logistics/driver-license-categories/seed
POST   /api/logistics/driver-licenses/{license_id}/categories
POST   /api/logistics/drivers
POST   /api/logistics/drivers/duplicate-check
POST   /api/logistics/drivers/{driver_id}/activate
POST   /api/logistics/drivers/{driver_id}/block
POST   /api/logistics/drivers/{driver_id}/carrier-assignments
POST   /api/logistics/drivers/{driver_id}/contacts
POST   /api/logistics/drivers/{driver_id}/documents
POST   /api/logistics/drivers/{driver_id}/identity-documents
POST   /api/logistics/drivers/{driver_id}/licenses
POST   /api/logistics/drivers/{driver_id}/photos
POST   /api/logistics/drivers/{driver_id}/restrictions
POST   /api/logistics/drivers/{driver_id}/unblock
POST   /api/logistics/drivers/{driver_id}/vehicle-compatibility
POST   /api/logistics/files/evidence
POST   /api/logistics/files/evidence/{evidence_id}/accept
POST   /api/logistics/files/upload-sessions
POST   /api/logistics/files/upload-sessions/{session_id}/finalize
POST   /api/logistics/files/{file_id}/archive
POST   /api/logistics/files/{file_id}/associations
POST   /api/logistics/files/{file_id}/legal-holds
POST   /api/logistics/files/{file_id}/request-deletion
POST   /api/logistics/files/{file_id}/restore
POST   /api/logistics/gate-check-in-corrections/{correction_id}/approve
POST   /api/logistics/gate-check-ins
POST   /api/logistics/gate-check-ins/walk-in
POST   /api/logistics/gate-check-ins/{check_in_id}/authorize-entry
POST   /api/logistics/gate-check-ins/{check_in_id}/authorize-with-observations
POST   /api/logistics/gate-check-ins/{check_in_id}/cancel
POST   /api/logistics/gate-check-ins/{check_in_id}/check-results
POST   /api/logistics/gate-check-ins/{check_in_id}/complete
POST   /api/logistics/gate-check-ins/{check_in_id}/corrections
POST   /api/logistics/gate-check-ins/{check_in_id}/deny-entry
POST   /api/logistics/gate-check-ins/{check_in_id}/documents
POST   /api/logistics/gate-check-ins/{check_in_id}/driver-inspection
POST   /api/logistics/gate-check-ins/{check_in_id}/exceptions
POST   /api/logistics/gate-check-ins/{check_in_id}/hold
POST   /api/logistics/gate-check-ins/{check_in_id}/issue-document
POST   /api/logistics/gate-check-ins/{check_in_id}/photo-upload-sessions
POST   /api/logistics/gate-check-ins/{check_in_id}/photos/associate
POST   /api/logistics/gate-check-ins/{check_in_id}/record-arrival
POST   /api/logistics/gate-check-ins/{check_in_id}/request-supervisor
POST   /api/logistics/gate-check-ins/{check_in_id}/resume
POST   /api/logistics/gate-check-ins/{check_in_id}/seal-inspection
POST   /api/logistics/gate-check-ins/{check_in_id}/start-verification
POST   /api/logistics/gate-check-ins/{check_in_id}/validate-decision
POST   /api/logistics/gate-check-ins/{check_in_id}/vehicle-inspection
POST   /api/logistics/gate-control/resolve-appointment
POST   /api/logistics/gate-verification-exceptions/{exception_id}/approve
POST   /api/logistics/gate-verification-exceptions/{exception_id}/reject
POST   /api/logistics/inbound-dock-assignments
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/cancel
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/confirm-dock-arrival
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/mark-ready
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/reassign
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/release-dock
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/request-reassignment
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/start-movement
POST   /api/logistics/inbound-dock-assignments/{assignment_id}/unloading-operation
POST   /api/logistics/inbound-dock-queue/from-gate-check-in
POST   /api/logistics/inbound-dock-queue/{queue_entry_id}/change-priority
POST   /api/logistics/inbound-dock-queue/{queue_entry_id}/hold
POST   /api/logistics/inbound-dock-queue/{queue_entry_id}/mark-ready
POST   /api/logistics/inbound-dock-queue/{queue_entry_id}/remove
POST   /api/logistics/inbound-dock-queue/{queue_entry_id}/resume
POST   /api/logistics/inbound/document-package/manifest
POST   /api/logistics/inbound/documents/{document_type_code}/pdf
POST   /api/logistics/inbound/documents/{document_type_code}/preview
POST   /api/logistics/inventory/document-package/manifest
POST   /api/logistics/inventory/documents/{document_type_code}/pdf
POST   /api/logistics/inventory/documents/{document_type_code}/preview
POST   /api/logistics/me/context
POST   /api/logistics/organizations
POST   /api/logistics/organizations/{organization_id}/branches
POST   /api/logistics/outbound/document-package/manifest
POST   /api/logistics/outbound/document-package/preview
POST   /api/logistics/outbound/documents/{document_type_code}/pdf
POST   /api/logistics/outbound/documents/{document_type_code}/preview
POST   /api/logistics/procurement-approvals/assignments/{assignment_id}/decision
POST   /api/logistics/procurement-approvals/policies
POST   /api/logistics/procurement-approvals/policy-versions/{version_id}/activate
POST   /api/logistics/procurement-approvals/policy-versions/{version_id}/conditions
POST   /api/logistics/procurement-approvals/policy-versions/{version_id}/steps
POST   /api/logistics/procurement-approvals/requests
POST   /api/logistics/procurement/purchase-orders/plan-generation
POST   /api/logistics/procurement/purchase-orders/{po_id}/approve
POST   /api/logistics/procurement/purchase-orders/{po_id}/cancel
POST   /api/logistics/procurement/purchase-orders/{po_id}/reject
POST   /api/logistics/procurement/purchase-orders/{po_id}/return-for-changes
POST   /api/logistics/procurement/purchase-orders/{po_id}/submit
POST   /api/logistics/procurement/requisitions
POST   /api/logistics/procurement/requisitions/{requisition_id}/approve
POST   /api/logistics/procurement/requisitions/{requisition_id}/cancel
POST   /api/logistics/procurement/requisitions/{requisition_id}/comments
POST   /api/logistics/procurement/requisitions/{requisition_id}/document/issue
POST   /api/logistics/procurement/requisitions/{requisition_id}/lines
POST   /api/logistics/procurement/requisitions/{requisition_id}/lines/reorder
POST   /api/logistics/procurement/requisitions/{requisition_id}/reject
POST   /api/logistics/procurement/requisitions/{requisition_id}/return
POST   /api/logistics/procurement/requisitions/{requisition_id}/start-review
POST   /api/logistics/procurement/requisitions/{requisition_id}/submit
POST   /api/logistics/procurement/requisitions/{requisition_id}/validate
POST   /api/logistics/procurement/requisitions/{requisition_id}/withdraw
POST   /api/logistics/product-brands
POST   /api/logistics/product-categories
POST   /api/logistics/products
POST   /api/logistics/products/{product_id}/identifiers
POST   /api/logistics/products/{product_id}/location-compatibility
POST   /api/logistics/products/{product_id}/packaging-definitions
POST   /api/logistics/products/{product_id}/sku
POST   /api/logistics/products/{product_id}/status
POST   /api/logistics/products/{product_id}/storage-conditions
POST   /api/logistics/products/{product_id}/unit-conversions/decompose
POST   /api/logistics/purchasing/documents/{document_type_code}/pdf
POST   /api/logistics/purchasing/documents/{document_type_code}/preview
POST   /api/logistics/reception-appointment-holds
POST   /api/logistics/reception-appointment-holds/{hold_id}/cancel
POST   /api/logistics/reception-appointment-holds/{hold_id}/refresh
POST   /api/logistics/reception-appointments
POST   /api/logistics/reception-appointments/{appointment_id}/cancel
POST   /api/logistics/reception-appointments/{appointment_id}/confirm
POST   /api/logistics/reception-appointments/{appointment_id}/issue
POST   /api/logistics/reception-appointments/{appointment_id}/package
POST   /api/logistics/reception-appointments/{appointment_id}/request-reschedule
POST   /api/logistics/reception-appointments/{appointment_id}/reschedule
POST   /api/logistics/reception-appointments/{appointment_id}/validate
POST   /api/logistics/reception-calendars
POST   /api/logistics/reception-calendars/{calendar_id}/activate
POST   /api/logistics/reception-calendars/{calendar_id}/archive
POST   /api/logistics/reception-calendars/{calendar_id}/availability
POST   /api/logistics/reception-calendars/{calendar_id}/blackouts
POST   /api/logistics/reception-calendars/{calendar_id}/deactivate
POST   /api/logistics/reception-calendars/{calendar_id}/operating-windows
POST   /api/logistics/role-assignments
POST   /api/logistics/role-assignments/validate-conflicts
POST   /api/logistics/role-assignments/{assignment_id}/revoke
POST   /api/logistics/ruc/assisted-verifications
POST   /api/logistics/ruc/assisted-verifications/{verification_id}/approve
POST   /api/logistics/ruc/business-partners/{partner_id}/apply-ruc-data
POST   /api/logistics/ruc/business-partners/{partner_id}/verify-ruc
POST   /api/logistics/ruc/datasets/{dataset_id}/activate
POST   /api/logistics/ruc/datasets/{source_id}/rollback
POST   /api/logistics/ruc/imports
POST   /api/logistics/security/step-up/challenges
POST   /api/logistics/security/step-up/challenges/{challenge_id}/complete
POST   /api/logistics/security/step-up/challenges/{challenge_id}/factors
POST   /api/logistics/supplier-evaluations/evaluations
POST   /api/logistics/supplier-evaluations/evaluations/{evaluation_id}/calculate
POST   /api/logistics/supplier-evaluations/evaluations/{evaluation_id}/decisions
POST   /api/logistics/supplier-evaluations/evaluations/{evaluation_id}/manual-scores
POST   /api/logistics/supplier-evaluations/templates
POST   /api/logistics/supplier-evaluations/templates/{template_id}/versions
POST   /api/logistics/supplier-evaluations/versions/{version_id}/activate
POST   /api/logistics/transport/document-package/manifest
POST   /api/logistics/transport/document-package/preview
POST   /api/logistics/transport/documents/{document_type_code}/pdf
POST   /api/logistics/transport/documents/{document_type_code}/preview
POST   /api/logistics/unit-conversion-rules
POST   /api/logistics/unit-conversions/compare
POST   /api/logistics/unit-conversions/evaluate
POST   /api/logistics/units
POST   /api/logistics/unloading-operations/{operation_id}/abort
POST   /api/logistics/unloading-operations/{operation_id}/cancel
POST   /api/logistics/unloading-operations/{operation_id}/complete
POST   /api/logistics/unloading-operations/{operation_id}/completion-checks
POST   /api/logistics/unloading-operations/{operation_id}/equipment
POST   /api/logistics/unloading-operations/{operation_id}/equipment/{equipment_assignment_id}/release
POST   /api/logistics/unloading-operations/{operation_id}/pause
POST   /api/logistics/unloading-operations/{operation_id}/readiness-checks
POST   /api/logistics/unloading-operations/{operation_id}/readiness-checks/{result_id}/approve-override
POST   /api/logistics/unloading-operations/{operation_id}/readiness-checks/{result_id}/reject-override
POST   /api/logistics/unloading-operations/{operation_id}/readiness-checks/{result_id}/request-override
POST   /api/logistics/unloading-operations/{operation_id}/responsibles
POST   /api/logistics/unloading-operations/{operation_id}/responsibles/{responsible_id}/accept
POST   /api/logistics/unloading-operations/{operation_id}/responsibles/{responsible_id}/release
POST   /api/logistics/unloading-operations/{operation_id}/responsibles/{responsible_id}/revoke
POST   /api/logistics/unloading-operations/{operation_id}/resume
POST   /api/logistics/unloading-operations/{operation_id}/seal-opening
POST   /api/logistics/unloading-operations/{operation_id}/start
POST   /api/logistics/unloading-operations/{operation_id}/time-corrections
POST   /api/logistics/unloading-operations/{operation_id}/time-corrections/{correction_id}/approve
POST   /api/logistics/unloading-operations/{operation_id}/time-corrections/{correction_id}/reject
POST   /api/logistics/unloading-operations/{operation_id}/validate-readiness
POST   /api/logistics/unloading-pauses/{pause_id}/cancel
POST   /api/logistics/unloading-pauses/{pause_id}/resume
POST   /api/logistics/unloading-readiness-check-results/{result_id}/approve-override
POST   /api/logistics/unloading-readiness-check-results/{result_id}/reject-override
POST   /api/logistics/unloading-readiness-check-results/{result_id}/request-override
POST   /api/logistics/unloading-responsible-assignments/{assignment_id}/accept
POST   /api/logistics/unloading-responsible-assignments/{assignment_id}/release
POST   /api/logistics/unloading-responsible-assignments/{assignment_id}/revoke
POST   /api/logistics/vehicle-makes
POST   /api/logistics/vehicle-models
POST   /api/logistics/vehicle-verification-sources/seed
POST   /api/logistics/vehicle-verifications/{verification_id}/apply
POST   /api/logistics/vehicles
POST   /api/logistics/vehicles/{vehicle_id}/activate
POST   /api/logistics/vehicles/{vehicle_id}/assisted-verifications
POST   /api/logistics/vehicles/{vehicle_id}/block
POST   /api/logistics/vehicles/{vehicle_id}/capacity-profiles
POST   /api/logistics/vehicles/{vehicle_id}/carrier-assignments
POST   /api/logistics/vehicles/{vehicle_id}/documents
POST   /api/logistics/vehicles/{vehicle_id}/owner-assignments
POST   /api/logistics/vehicles/{vehicle_id}/plate-change
POST   /api/logistics/vehicles/{vehicle_id}/unblock
POST   /api/logistics/vehicles/{vehicle_id}/verifications
POST   /api/logistics/warehouse-dock-blackouts/{blackout_id}/cancel
POST   /api/logistics/warehouse-dock-operating-windows/{window_id}/deactivate
POST   /api/logistics/warehouse-docks
POST   /api/logistics/warehouse-docks/{dock_id}/activate
POST   /api/logistics/warehouse-docks/{dock_id}/archive
POST   /api/logistics/warehouse-docks/{dock_id}/blackouts
POST   /api/logistics/warehouse-docks/{dock_id}/blackouts/{blackout_id}/cancel
POST   /api/logistics/warehouse-docks/{dock_id}/block
POST   /api/logistics/warehouse-docks/{dock_id}/capabilities
POST   /api/logistics/warehouse-docks/{dock_id}/deactivate
POST   /api/logistics/warehouse-docks/{dock_id}/mark-maintenance
POST   /api/logistics/warehouse-docks/{dock_id}/operating-windows
POST   /api/logistics/warehouse-docks/{dock_id}/unblock
POST   /api/logistics/warehouse-gates
POST   /api/logistics/warehouse-gates/{gate_id}/activate
POST   /api/logistics/warehouse-gates/{gate_id}/archive
POST   /api/logistics/warehouse-gates/{gate_id}/deactivate
POST   /api/logistics/warehouses
POST   /api/logistics/warehouses/layouts/{layout_version_id}/activate
POST   /api/logistics/warehouses/layouts/{layout_version_id}/nodes
POST   /api/logistics/warehouses/locations/labels/export
POST   /api/logistics/warehouses/locations/{location_id}/capacities
POST   /api/logistics/warehouses/locations/{location_id}/move
POST   /api/logistics/warehouses/locations/{location_id}/move-preview
POST   /api/logistics/warehouses/locations/{location_id}/qr/rotate
POST   /api/logistics/warehouses/locations/{location_id}/restrictions
POST   /api/logistics/warehouses/{warehouse_id}/bulk-locations/execute
POST   /api/logistics/warehouses/{warehouse_id}/bulk-locations/preview
POST   /api/logistics/warehouses/{warehouse_id}/layouts
POST   /api/logistics/warehouses/{warehouse_id}/locations
POST   /api/logistics/warehouses/{warehouse_id}/set-default
POST   /api/logistics/warehouses/{warehouse_id}/status
POST   /api/research/consent
POST   /api/research/consent/withdraw
POST   /api/research/participants
POST   /api/research/participants/self-enroll
POST   /api/research/participants/{participant_id}/withdraw
POST   /api/research/sessions/start
POST   /api/research/sessions/{session_id}/behavior-batches
POST   /api/research/sessions/{session_id}/cancel
POST   /api/research/sessions/{session_id}/face-captures
POST   /api/research/sessions/{session_id}/finish
POST   /api/routes
POST   /api/routes/{route_id}/assign-shipments
POST   /api/shipments
POST   /api/shipments/{shipment_id}/status
POST   /api/warehouses
PUT    /api/logistics/arrival-notice-revisions/{revision_id}/driver-reference
PUT    /api/logistics/arrival-notice-revisions/{revision_id}/vehicle-reference
PUT    /api/logistics/documents/{document_id}
PUT    /api/logistics/products/{product_id}/physical-profile
PUT    /api/logistics/products/{product_id}/tracking-policy
PUT    /api/logistics/products/{product_id}/unit-configuration
PUT    /api/logistics/warehouses/locations/{location_id}
PUT    /api/logistics/warehouses/{warehouse_id}
```

## FIN DEL PROMPT
