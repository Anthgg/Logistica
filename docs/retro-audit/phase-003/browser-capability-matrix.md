# Matriz de Capacidades Backend ↔ Frontend y Registro de Gaps · Fase 003

## 1. Visión General de la Matriz

Esta matriz desglosa las capacidades funcionales provistas por el backend (`backend/app/modules/logistics/` y endpoints raíz relacionados), evalúa su estado de integración en la interfaz React (`frontend/src/`) y asigna de forma vinculante (`MANDATORY_AT_OWNER_PHASE = TRUE`) cada brecha funcional a su fase propietaria en el Plan Maestro (F004 a F100).

---

## 2. Matriz de Capacidades Funcionales por Dominio

### Dominio 1: Estructura Organizacional, Sedes y Almacenes (F004)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Organizaciones (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/organizations` | `api/company-profile-api.ts` | `/logistics/organizations` | `OrganizationsPage.tsx` | `PARTIAL` | `F003-GAP-001` → **F004** |
| **Sedes / Branches (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/branches` | `api/company-profile-api.ts` | `/logistics/branches` | `BranchesPage.tsx` | `PARTIAL` | `F003-GAP-002` → **F004** |
| **Almacenes y Zonas (CRUD)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/warehouses` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses` | `WarehousesPage.tsx`, `WarehouseDetailPage.tsx` | `INTEGRATED` | `F003-GAP-003` → **F004** |
| **Etiquetas QR de Ubicación** | `GET (pdf/single)`, `POST (batch)` | `/api/logistics/warehouses/locations/labels/batch` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses/:id` | `WarehouseDetailPage.tsx` | `PARTIAL` | `F003-GAP-004` → **F004** |

---

### Dominio 2: Seguridad, Roles, Permisos y Step-Up (F005, F006, F008, F009)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Permisos RBAC** | `GET` | `/api/logistics/rbac/permissions` | `api/logistics-api.ts` | `/logistics/permissions` | `PermissionsCatalogPage.tsx` | `INTEGRATED` | - |
| **Gestión de Roles RBAC** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/rbac/roles` | `features/logistics-permissions/api/*` | `/logistics/roles` | `RolesPage.tsx` | `PARTIAL` | `F003-GAP-005` → **F005** |
| **Asignación de Roles a Usuarios** | `GET`, `POST`, `DELETE` | `/api/logistics/rbac/assignments` | `features/logistics-permissions/api/*` | `/logistics/role-assignments` | `RoleAssignmentsPage.tsx` | `PARTIAL` | `F003-GAP-006` → **F006** |
| **Autenticación Continua & Step-Up**| `POST`, `GET` | `/api/logistics/security/step-up/*` | `features/continuous-auth/api/*` | Modal Global | `ContinuousAuthProvider.tsx` | `INTEGRATED` | - |

---

### Dominio 3: Auditoría y Trazabilidad (F007)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Visor de Eventos de Auditoría** | `GET` | `/api/logistics/audit/events` | `api/logistics-api.ts` | `/logistics/audit-events` | `AuditEventsPage.tsx` | `INTEGRATED` | - |
| **Exportación de Logs de Auditoría**| `POST` | `/api/logistics/audit/export` | *Sin cliente específico* | - | - | `FRONTEND_MISSING` | `F003-GAP-007` → **F007** |

---

### Dominio 4: Custodia de Archivos y Evidencias (F010)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Repositorio Seguro de Archivos** | `GET`, `POST` | `/api/logistics/files` | `api/files-api.ts` | `/logistics/files` | `FilesRepositoryPage.tsx` | `INTEGRATED` | - |
| **Carga Chunked / Sesiones** | `POST (init/chunk/finish)` | `/api/logistics/files/upload-sessions` | `api/files-api.ts` | `/logistics/files/upload` | `FileUploadPage.tsx` | `INTEGRATED` | - |
| **Solicitud de Borrado Legal** | `POST`, `GET` | `/api/logistics/files/deletion-requests`| `api/files-api.ts` | `/logistics/file-deletion-requests` | `FileDeletionRequestsPage.tsx` | `INTEGRATED` | - |

---

### Dominio 5: Motor Documental y Series (F011 - F020)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Familias y Tipos** | `GET` | `/api/logistics/documents/types` | `api/documents-api.ts` | `/logistics/documents` | `DocumentsPage.tsx` | `INTEGRATED` | - |
| **Talonarios y Series Correlativas**| `GET`, `POST`, `PATCH` | `/api/logistics/documents/series`, `/talonarios` | `api/documents-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-008` → **F013** |
| **Editor de Plantillas Documentales**| `GET`, `POST`, `PUT` | `/api/logistics/documents/templates` | `api/documents-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-009` → **F014** |
| **Generación de Paquetes ZIP** | `POST`, `GET` | `/api/logistics/documents/packages` | `api/documents-api.ts` | Modal en documentos | `DocumentsPage.tsx` | `PARTIAL` | `F003-GAP-010` → **F017** |

---

### Dominio 6: Catálogo de Productos y Unidades (F021 - F030)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Productos y SKUs** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/products` | `api/products-catalog-api.ts` | `/logistics/catalog/products` | `ProductsPage.tsx`, `ProductDetailPage.tsx` | `INTEGRATED` | - |
| **Unidades y Factores de Conversión**| `GET`, `POST`, `PUT` | `/api/logistics/units` | `api/units-conversions-api.ts` | `/logistics/catalog/units` | `UnitsAndConversionsPage.tsx` | `INTEGRATED` | - |
| **Matriz de Compatibilidad de SKUs**| `POST`, `GET` | `/api/logistics/products/compatibility`| `api/products-catalog-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-011` → **F022** |

---

### Dominio 7: Compras y Requisiciones (F031 - F035)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Requisiciones de Compra (PR)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/procurement/requisitions` | `api/purchase-requisitions-api.ts` | `/logistics/purchasing/requisitions` | `PurchaseRequisitionsPage.tsx`, `PurchaseRequisitionFormPage.tsx` | `INTEGRATED` | - |
| **Bandeja de Aprobaciones Multinivel**| `GET`, `POST (approve/reject)` | `/api/logistics/procurement/approvals` | `features/procurement-approvals/api/*`| `/logistics/purchasing/approvals` | `ApprovalInboxPage.tsx`, `ApprovalPoliciesPage.tsx` | `INTEGRATED` | - |
| **Órdenes de Compra (PO)** | `GET`, `POST`, `PATCH (amend/cancel)` | `/api/logistics/procurement/purchase-orders` | `api/purchase-orders-api.ts`, `features/purchase-orders/api/*` | `/logistics/purchasing/orders` | `PurchaseOrdersPage.tsx`, `PurchaseOrderDetailPage.tsx` | `INTEGRATED` | - |
| **Evaluación de Cotizaciones** | `GET`, `POST`, `PUT` | `/api/logistics/procurement/evaluations` | `features/supplier-evaluation/api/*` | `/logistics/purchasing/evaluations` | `QuotationEvaluationsPage.tsx` | `INTEGRATED` | - |

---

### Dominio 8: Recepción, Garita y Calidad (F036 - F043)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Control de Garita y Pesaje** | `GET`, `POST`, `PATCH` | `/api/logistics/inbound/gate-control` | `features/gate-control/api/*` | `/logistics/inbound/gate-control` | `GateControlDashboardPage.tsx`, `CreateGateCheckInPage.tsx` | `INTEGRATED` | - |
| **Gestión de Muelles (Docks)** | `GET`, `POST`, `PUT` | `/api/logistics/inbound/docks` | `features/inbound-docks/api/*` | `/logistics/inbound/docks` | `WarehouseDocksSettingsPage.tsx` | `INTEGRATED` | - |
| **Escaneo de Bultos / Recepción**| `GET`, `POST` | `/api/logistics/inbound/receptions` | `features/inbound-receiving/api/*` | `/logistics/inbound/receiving` | `InboundReceivingPage.tsx` | `INTEGRATED` | - |
| **Planes de Inspección de Calidad**| `GET`, `POST`, `PUT` | `/api/logistics/inbound/quality-plans` | `features/quality-inspection-plans/api/*` | `/logistics/quality/plans` | `QualityInspectionPlansPage.tsx` | `INTEGRATED` | - |
| **Gestión de Cuarentena** | `GET`, `POST (release/reject)` | `/api/logistics/inbound/quarantine` | `features/quarantine/api/*` | `/logistics/quality/quarantine-zones` | `QualityQuarantineDashboardPage.tsx` | `INTEGRATED` | - |
| **Diferencias y Mermas** | `GET`, `POST (resolve)` | `/api/logistics/inbound/differences` | `features/reception-differences/api/*` | `/logistics/inbound/differences` | `ReceptionDifferenceCasesPage.tsx` | `INTEGRATED` | - |

---

### Dominio 9: Inventario, Kárdex y Balances (F044 - F050)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kárdex y Movimientos Ledger** | `GET`, `POST` | `/api/logistics/inventory/ledger` | `features/inventory-ledger/api/*` | `/logistics/inventory/ledger` | `InventoryMovementsPage.tsx`, `InventoryKardexPage.tsx` | `INTEGRATED` | - |
| **Saldos por Ubicación y Lote** | `GET` | `/api/logistics/inventory/balances` | `features/inventory-balances/api/*` | `/logistics/inventory/balances` | `InventoryBalancesPage.tsx`, `InventoryWarehouseBalancesPage.tsx` | `INTEGRATED` | - |
| **Motor de Putaway Asistido** | `GET`, `POST (execute)` | `/api/logistics/inventory/putaway` | `features/putaway/api/*` | `/logistics/inventory/putaway` | `PutawayDashboardPage.tsx`, `PutawayOrdersPage.tsx` | `INTEGRATED` | - |
| **Reconciliación y Conteo Físico** | `POST`, `GET` | `/api/logistics/inventory/reconciliation` | `features/inventory-ledger/api/*` | `/logistics/inventory/reconciliation` | `InventoryLedgerReconciliationPage.tsx` | `INTEGRATED` | - |

---

### Dominio 10: Despacho, Transporte y Entrega (F051 - F080)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gestión de Flota Vehicular** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/vehicles` | `api/vehicles-api.ts` | `/logistics/vehicles` | `VehiclesPage.tsx`, `VehicleDetailPage.tsx` | `INTEGRATED` | - |
| **Gestión de Conductores y MTC** | `GET`, `POST`, `PUT` | `/api/logistics/drivers` | `api/drivers-api.ts` | `/logistics/drivers` | `DriversPage.tsx`, `DriverDetailPage.tsx` | `INTEGRATED` | - |
| **Verificación Técnica Vehicular** | `GET`, `POST`, `PATCH` | `/api/logistics/vehicle-verifications` | `api/vehicle-verifications-api.ts` | `/logistics/vehicle-verifications` | `VehicleVerificationsPage.tsx` | `INTEGRATED` | - |
| **Gestión de Envíos / Shipments** | `GET`, `POST`, `PATCH` | `/api/shipments` | `api/shipment-contracts.ts` | `/shipments` | `ShipmentsPage.tsx`, `ShipmentDetailPage.tsx` | `PARTIAL` | `F003-GAP-012` → **F051** |
| **Asignación Avanzada de Despacho**| `POST` | `/api/logistics/documents/rendering/dispatch` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-013` → **F053** |
| **Prueba Electrónica de Entrega (POD)**| `POST` | `/api/logistics/documents/rendering/delivery` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-014` → **F072** |

---

### Dominio 11: Integraciones y Padrón SUNAT RUC (F081 - F090)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Consulta Interactiva de RUC** | `GET`, `POST` | `/api/logistics/ruc` | `api/ruc-integration-api.ts` | `/logistics/ruc-integration` | `RucIntegrationPage.tsx` | `INTEGRATED` | - |
| **Sincronización Masiva en Batch** | `POST` | `/api/logistics/ruc/sync-batch` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-015` → **F083** |

---

### Dominio 12: KPIs e Indicadores Ejecutivos (F091 - F100)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard Operativo General** | `GET` | `/api/dashboard` | `api/operations-api.ts` | `/dashboard` | `DashboardPage.tsx` | `INTEGRATED` | - |
| **Reportes y Exportación** | `GET`, `POST` | `/api/reports` | `api/operations-api.ts` | `/reports` | `ReportsPage.tsx` | `INTEGRATED` | - |
| **Diseñador de Widgets de KPIs** | `POST`, `PUT` | `/api/dashboard/widgets` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-016` → **F092** |

---

## 3. Registro Vinculante de Gaps Frontend (Mandatory at Owner Phase)

| GAP_ID | Capacidad Backend Afectada | Estado Frontend Actual | OWNER_PHASE | MANDATORY_AT_OWNER_PHASE | Razón y Criterio de Bloqueo |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **F003-GAP-001** | Edición y actualización de Organizaciones (`PATCH /api/organizations/{id}`) | Modal de edición no implementado | **F004** | `TRUE` | La definición de organizaciones en F004 exige ciclo completo de mantenimiento. |
| **F003-GAP-002** | Desactivación y borrado lógico de Sedes (`DELETE /api/branches/{id}`) | Acción no disponible en UI | **F004** | `TRUE` | Requerido para gestión de ciclo de vida de sedes en F004. |
| **F003-GAP-003** | Edición masiva de ubicaciones de almacén | Formulario unitario únicamente | **F004** | `TRUE` | Requerido para modelado ágil de almacenes en F004. |
| **F003-GAP-004** | Generación por lote de etiquetas QR de almacén (`/locations/labels/batch`) | Generación unitaria únicamente | **F004** | `TRUE` | Impresión de rotulados por zona de almacén en F004. |
| **F003-GAP-005** | Creación y edición interactiva de Roles RBAC | Listado de solo lectura | **F005** | `TRUE` | F005 tiene como objetivo oficial la definición de roles del sistema. |
| **F003-GAP-006** | Asignación y revocación dinámica de roles a usuarios | Formulario manual básico | **F006** | `TRUE` | F006 tiene como objetivo oficial la gestión de permisos y asignaciones. |
| **F003-GAP-007** | Exportación de logs de auditoría a CSV/JSON | Visualización en pantalla únicamente | **F007** | `TRUE` | F007 audita la trazabilidad integral y exportación para cumplimiento. |
| **F003-GAP-008** | Mantenimiento de Series y Talonarios correlativos | Operativo únicamente vía API backend | **F013** | `TRUE` | F013 corresponde formalmente a la configuración de talonarios y series. |
| **F003-GAP-009** | Editor visual de plantillas HTML/PDF de documentos | Configuración estática en código | **F014** | `TRUE` | F014 tiene como alcance el motor de plantillas y personalización. |
| **F003-GAP-010** | Descarga masiva de paquetes documentales ZIP | Descarga individual de PDF | **F017** | `TRUE` | F017 corresponde al empaquetado documental de despachos. |
| **F003-GAP-011** | Matriz visual de compatibilidad química/técnica de SKUs | Validación interna en backend | **F022** | `TRUE` | F022 audita las reglas de almacenamiento y zonificación de productos. |
| **F003-GAP-012** | Integración avanzada de envíos con manifiestos de despacho | Tracking básico de estados | **F051** | `TRUE` | F051 inicia el dominio de Salida y Despacho. |
| **F003-GAP-013** | Orquestación interactiva de asignación de carga vehicular | Endpoints backend sin pantalla | **F053** | `TRUE` | F053 corresponde a la asignación de pedidos a unidades de transporte. |
| **F003-GAP-014** | Captura móvil de firma digital y fotos de entrega (POD) | Visor de comprobante generado | **F072** | `TRUE` | F072 audita la prueba electrónica de entrega en destino. |
| **F003-GAP-015** | Sincronización en segundo plano de padrón masivo SUNAT | Búsqueda unitaria interactiva | **F083** | `TRUE` | F083 corresponde a la sincronización de padrones de contribuyentes. |
| **F003-GAP-016** | Constructor interactivo de paneles y widgets de KPIs | Tableros predefinidos | **F092** | `TRUE` | F092 corresponde a la personalización de analítica ejecutiva. |
