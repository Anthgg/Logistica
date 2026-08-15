# Matriz de Capacidades Backend ↔ Frontend y Registro de Gaps · Fase 003

## 1. Visión General de la Matriz

Esta matriz desglosa las capacidades funcionales provistas por el backend (`backend/app/modules/logistics/` y endpoints raíz relacionados), evalúa su estado de integración en la interfaz React (`frontend/src/`) y asigna de forma vinculante (`MANDATORY_AT_OWNER_PHASE = TRUE`) cada brecha funcional a su fase propietaria en el Plan Maestro oficial (F004 a F100).

---

## 2. Matriz de Capacidades Funcionales por Dominio

### Dominio 1: Estructura Organizacional, Sedes y Almacenes (F004, F021, F022)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Organizaciones (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/organizations` | `api/company-profile-api.ts` | `/logistics/organizations` | `OrganizationsPage.tsx` | `PARTIAL` | `F003-GAP-001` → **F004** |
| **Sedes / Branches (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/branches` | `api/company-profile-api.ts` | `/logistics/branches` | `BranchesPage.tsx` | `PARTIAL` | `F003-GAP-002` → **F004** |
| **Almacenes y Zonas (CRUD)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/warehouses` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses` | `WarehousesPage.tsx`, `WarehouseDetailPage.tsx` | `INTEGRATED` | `-` |
| **Modelado de Posiciones y Racks** | `GET`, `POST`, `PUT` | `/api/logistics/warehouses/locations` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses/:id` | `WarehouseDetailPage.tsx` | `PARTIAL` | `F003-GAP-003` → **F022** |
| **Etiquetas QR en Batch** | `POST (batch)` | `/api/logistics/warehouses/locations/labels/batch` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses/:id` | `WarehouseDetailPage.tsx` | `PARTIAL` | `F003-GAP-004` → **F022** |

---

### Dominio 2: Seguridad, Roles, Permisos y Step-Up (F005, F006, F008, F009)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Permisos RBAC** | `GET` | `/api/logistics/rbac/permissions` | `api/logistics-api.ts` | `/logistics/permissions` | `PermissionsCatalogPage.tsx` | `INTEGRATED` | `-` |
| **Gestión de Roles RBAC** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/rbac/roles` | `features/logistics-permissions/api/*` | `/logistics/roles` | `RolesPage.tsx` | `PARTIAL` | `F003-GAP-005` → **F005** |
| **Asignación de Roles a Usuarios** | `GET`, `POST`, `DELETE` | `/api/logistics/rbac/assignments` | `features/logistics-permissions/api/*` | `/logistics/role-assignments` | `RoleAssignmentsPage.tsx` | `PARTIAL` | `F003-GAP-006` → **F006** |
| **Autenticación Continua & Step-Up**| `POST`, `GET` | `/api/logistics/security/step-up/*` | `features/continuous-auth/api/*` | Modal Global | `ContinuousAuthProvider.tsx` | `INTEGRATED` | `-` |

---

### Dominio 3: Auditoría y Trazabilidad (F007)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Visor de Eventos de Auditoría** | `GET` | `/api/logistics/audit/events` | `api/logistics-api.ts` | `/logistics/audit-events` | `AuditEventsPage.tsx` | `INTEGRATED` | `-` |
| **Exportación de Logs de Auditoría**| `POST` | `/api/logistics/audit/export` | *Sin cliente específico* | - | - | `FRONTEND_MISSING` | `F003-GAP-007` → **F007** |

---

### Dominio 4: Custodia de Archivos y Evidencias (F030)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Repositorio Seguro de Archivos** | `GET`, `POST` | `/api/logistics/files` | `api/files-api.ts` | `/logistics/files` | `FilesRepositoryPage.tsx` | `INTEGRATED` | `-` |
| **Carga Chunked / Sesiones** | `POST (init/chunk/finish)` | `/api/logistics/files/upload-sessions` | `api/files-api.ts` | `/logistics/files/upload` | `FileUploadPage.tsx` | `INTEGRATED` | `-` |
| **Solicitud de Borrado Legal** | `POST`, `GET` | `/api/logistics/files/deletion-requests`| `api/files-api.ts` | `/logistics/file-deletion-requests` | `FileDeletionRequestsPage.tsx` | `INTEGRATED` | `-` |

---

### Dominio 5: Motor Documental y Series (F011 - F020)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Familias y Tipos** | `GET` | `/api/logistics/documents/types` | `api/documents-api.ts` | `/logistics/documents` | `DocumentsPage.tsx` | `INTEGRATED` | `-` |
| **Talonarios y Series Correlativas**| `GET`, `POST`, `PATCH` | `/api/logistics/documents/series`, `/talonarios` | `api/documents-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-008` → **F013** |
| **Editor de Plantillas Documentales**| `GET`, `POST`, `PUT` | `/api/logistics/documents/templates` | `api/documents-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-009` → **F014** |
| **Generación de Paquetes ZIP** | `POST`, `GET` | `/api/logistics/documents/packages` | `api/documents-api.ts` | Modal en documentos | `DocumentsPage.tsx` | `PARTIAL` | `F003-GAP-010` → **F020** |

---

### Dominio 6: Catálogo de Productos y Unidades (F023, F024)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catálogo de Productos y SKUs** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/products` | `api/products-catalog-api.ts` | `/logistics/catalog/products` | `ProductsPage.tsx`, `ProductDetailPage.tsx` | `INTEGRATED` | `-` |
| **Unidades y Factores de Conversión**| `GET`, `POST`, `PUT` | `/api/logistics/units` | `api/units-conversions-api.ts` | `/logistics/catalog/units` | `UnitsAndConversionsPage.tsx` | `INTEGRATED` | `-` |
| **Matriz de Compatibilidad de SKUs**| `POST`, `GET` | `/api/logistics/products/compatibility`| `api/products-catalog-api.ts` | - | - | `FRONTEND_MISSING` | `F003-GAP-011` → **F023** |

---

### Dominio 7: Compras y Requisiciones (F031 - F035)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Requisiciones de Compra (PR)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/procurement/requisitions` | `api/purchase-requisitions-api.ts` | `/logistics/purchasing/requisitions` | `PurchaseRequisitionsPage.tsx`, `PurchaseRequisitionFormPage.tsx` | `INTEGRATED` | `-` |
| **Bandeja de Aprobaciones Multinivel**| `GET`, `POST (approve/reject)` | `/api/logistics/procurement/approvals` | `features/procurement-approvals/api/*`| `/logistics/purchasing/approvals` | `ApprovalInboxPage.tsx`, `ApprovalPoliciesPage.tsx` | `INTEGRATED` | `-` |
| **Órdenes de Compra (PO)** | `GET`, `POST`, `PATCH (amend/cancel)` | `/api/logistics/procurement/purchase-orders` | `api/purchase-orders-api.ts`, `features/purchase-orders/api/*` | `/logistics/purchasing/orders` | `PurchaseOrdersPage.tsx`, `PurchaseOrderDetailPage.tsx` | `INTEGRATED` | `-` |
| **Evaluación de Cotizaciones** | `GET`, `POST`, `PUT` | `/api/logistics/procurement/evaluations` | `features/supplier-evaluation/api/*` | `/logistics/purchasing/evaluations` | `QuotationEvaluationsPage.tsx` | `INTEGRATED` | `-` |

---

### Dominio 8: Recepción, Garita y Calidad (F036 - F043)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Control de Garita y Pesaje** | `GET`, `POST`, `PATCH` | `/api/logistics/inbound/gate-control` | `features/gate-control/api/*` | `/logistics/inbound/gate-control` | `GateControlDashboardPage.tsx`, `CreateGateCheckInPage.tsx` | `INTEGRATED` | `-` |
| **Gestión de Muelles (Docks)** | `GET`, `POST`, `PUT` | `/api/logistics/inbound/docks` | `features/inbound-docks/api/*` | `/logistics/inbound/docks` | `WarehouseDocksSettingsPage.tsx` | `INTEGRATED` | `-` |
| **Escaneo de Bultos / Recepción**| `GET`, `POST` | `/api/logistics/inbound/receptions` | `features/inbound-receiving/api/*` | `/logistics/inbound/receiving` | `InboundReceivingPage.tsx` | `INTEGRATED` | `-` |
| **Planes de Inspección de Calidad**| `GET`, `POST`, `PUT` | `/api/logistics/inbound/quality-plans` | `features/quality-inspection-plans/api/*` | `/logistics/quality/plans` | `QualityInspectionPlansPage.tsx` | `INTEGRATED` | `-` |
| **Gestión de Cuarentena** | `GET`, `POST (release/reject)` | `/api/logistics/inbound/quarantine` | `features/quarantine/api/*` | `/logistics/quality/quarantine-zones` | `QualityQuarantineDashboardPage.tsx` | `INTEGRATED` | `-` |
| **Diferencias y Mermas** | `GET`, `POST (resolve)` | `/api/logistics/inbound/differences` | `features/reception-differences/api/*` | `/logistics/inbound/differences` | `ReceptionDifferenceCasesPage.tsx` | `INTEGRATED` | `-` |

---

### Dominio 9: Inventario, Kárdex y Balances (F044 - F050)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kárdex y Movimientos Ledger** | `GET`, `POST` | `/api/logistics/inventory/ledger` | `features/inventory-ledger/api/*` | `/logistics/inventory/ledger` | `InventoryMovementsPage.tsx`, `InventoryKardexPage.tsx` | `INTEGRATED` | `-` |
| **Saldos por Ubicación y Lote** | `GET` | `/api/logistics/inventory/balances` | `features/inventory-balances/api/*` | `/logistics/inventory/balances` | `InventoryBalancesPage.tsx`, `InventoryWarehouseBalancesPage.tsx` | `INTEGRATED` | `-` |
| **Motor de Putaway Asistido** | `GET`, `POST (execute)` | `/api/logistics/inventory/putaway` | `features/putaway/api/*` | `/logistics/inventory/putaway` | `PutawayDashboardPage.tsx`, `PutawayOrdersPage.tsx` | `INTEGRATED` | `-` |
| **Reconciliación y Conteo Físico** | `POST`, `GET` | `/api/logistics/inventory/reconciliation` | `features/inventory-ledger/api/*` | `/logistics/inventory/reconciliation` | `InventoryLedgerReconciliationPage.tsx` | `INTEGRATED` | `-` |

---

### Dominio 10: Despacho, Transporte y Entrega (F027, F028, F029, F051, F055, F072)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gestión de Flota Vehicular** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/vehicles` | `api/vehicles-api.ts` | `/logistics/vehicles` | `VehiclesPage.tsx`, `VehicleDetailPage.tsx` | `INTEGRATED` | `-` |
| **Gestión de Conductores y MTC** | `GET`, `POST`, `PUT` | `/api/logistics/drivers` | `api/drivers-api.ts` | `/logistics/drivers` | `DriversPage.tsx`, `DriverDetailPage.tsx` | `INTEGRATED` | `-` |
| **Verificación Técnica Vehicular** | `GET`, `POST`, `PATCH` | `/api/logistics/vehicle-verifications` | `api/vehicle-verifications-api.ts` | `/logistics/vehicle-verifications` | `VehicleVerificationsPage.tsx` | `INTEGRATED` | `-` |
| **Gestión de Envíos / Shipments** | `GET`, `POST`, `PATCH` | `/api/shipments` | `api/shipment-contracts.ts` | `/shipments` | `ShipmentsPage.tsx`, `ShipmentDetailPage.tsx` | `PARTIAL` | `F003-GAP-012` → **F051** |
| **Planificación y Asignación de Carga**| `POST` | `/api/logistics/documents/rendering/dispatch` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-013` → **F055** |
| **Prueba de Entrega (POD)** | `POST` | `/api/logistics/documents/rendering/delivery` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-014` → **F072** |

---

### Dominio 11: Integraciones y Padrón SUNAT RUC (F026)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Consulta Interactiva de RUC** | `GET`, `POST` | `/api/logistics/ruc` | `api/ruc-integration-api.ts` | `/logistics/ruc-integration` | `RucIntegrationPage.tsx` | `INTEGRATED` | `-` |
| **Sincronización Masiva en Batch** | `POST` | `/api/logistics/ruc/sync-batch` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-015` → **F026** |

---

### Dominio 12: KPIs e Indicadores Ejecutivos (F081, F088, F089)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend | Componente / Vista UI | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard Operativo General** | `GET` | `/api/dashboard` | `api/operations-api.ts` | `/dashboard` | `DashboardPage.tsx` | `INTEGRATED` | `-` |
| **Reportes y Exportación** | `GET`, `POST` | `/api/reports` | `api/operations-api.ts` | `/reports` | `ReportsPage.tsx` | `INTEGRATED` | `-` |
| **Constructor de Dashboards React** | `POST`, `PUT` | `/api/dashboard/widgets` | *Sin cliente dedicado* | - | - | `FRONTEND_MISSING` | `F003-GAP-016` → **F088** |

---

## 3. Registro Vinculante de Gaps Frontend (Mandatory at Owner Phase)

| GAP_ID | Capacidad Backend Afectada | Estado Frontend Actual | OWNER_PHASE | Título Canónico Plan Maestro | MANDATORY_AT_OWNER_PHASE | Requisitos de Prueba en Navegador en Owner Phase |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **F003-GAP-001** | Edición de Organizaciones (`PATCH /api/organizations/{id}`) | Modal de edición no implementado | **F004** | Definir organización, sedes y almacenes | `TRUE` | `CREATE`, `DETAIL`, `UPDATE` organización, persistencia F5, Network 200, Console 0 errores. |
| **F003-GAP-002** | Desactivación y baja de Sedes (`DELETE /api/branches/{id}`) | Acción no disponible en UI | **F004** | Definir organización, sedes y almacenes | `TRUE` | `CREATE`, `UPDATE`, `DEACTIVATE` sede, persistencia F5, comprobación de integridad referencial. |
| **F003-GAP-003** | Modelado de Racks y Posiciones de Almacén | Formulario unitario básico | **F022** | Modelar almacenes y ubicaciones | `TRUE` | Creación de zonas, pasillos, niveles y racks con visualización jerárquica. |
| **F003-GAP-004** | Generación por lote de etiquetas QR de almacén (`/locations/labels/batch`) | Generación unitaria únicamente | **F022** | Modelar almacenes y ubicaciones | `TRUE` | Selección múltiple de ubicaciones, descarga de PDF masivo y visualización de QR. |
| **F003-GAP-005** | Creación y edición interactiva de Roles RBAC | Listado de solo lectura | **F005** | Definir roles logísticos | `TRUE` | Creación de rol personalizado, asignación de nombre/código y persistencia F5. |
| **F003-GAP-006** | Asignación y revocación dinámica de roles a usuarios | Formulario manual básico | **F006** | Definir permisos por acción | `TRUE` | Asignación de rol a operador, verificación de permisos efectivos en `/logistics/me`. |
| **F003-GAP-007** | Exportación de logs de auditoría a CSV/JSON | Visualización en pantalla únicamente | **F007** | Unificar eventos de auditoría | `TRUE` | Filtrado por fechas/severidad y descarga de archivo de auditoría exportado. |
| **F003-GAP-008** | Mantenimiento de Series y Talonarios correlativos | Operativo únicamente vía API backend | **F013** | Diseñar series y talonarios | `TRUE` | Configuración de prefijos de serie, asignación de rangos numéricos y bloqueo por vencimiento. |
| **F003-GAP-009** | Editor visual de plantillas HTML/PDF de documentos | Configuración estática en código | **F014** | Crear el motor de plantillas | `TRUE` | Previsualización en tiempo real de variables documentales y guardado de versión de plantilla. |
| **F003-GAP-010** | Descarga masiva de paquetes documentales ZIP | Descarga individual de PDF | **F020** | Implementar descarga, reimpresión y anulación | `TRUE` | Generación y descarga de archivo comprimido con múltiples artefactos documentales. |
| **F003-GAP-011** | Matriz visual de compatibilidad química/técnica de SKUs | Validación interna en backend | **F023** | Crear el catálogo de productos | `TRUE` | Configuración de incompatibilidades entre familias de productos y alertas visuales. |
| **F003-GAP-012** | Integración avanzada de envíos con manifiestos de salida | Tracking básico de estados | **F051** | Implementar pedidos de salida | `TRUE` | Creación de orden de salida vinculada a inventario y actualización de línea de tiempo. |
| **F003-GAP-013** | Planificación interactiva de asignación de carga vehicular | Endpoints backend sin pantalla | **F055** | Planificar el despacho | `TRUE` | Asignación de pedidos a unidades vehiculares verificando restricciones de peso/volumen. |
| **F003-GAP-014** | Captura móvil de firma digital y fotos de entrega (POD) | Visor de comprobante generado | **F072** | Implementar prueba de entrega | `TRUE` | Registro de receptor, firma manuscrita digital, captura de coordenadas GPS y foto de entrega. |
| **F003-GAP-015** | Sincronización en segundo plano de padrón masivo SUNAT | Búsqueda unitaria interactiva | **F026** | Integrar consulta de RUC | `TRUE` | Carga de archivo de contribuyentes y actualización por lotes en segundo plano. |
| **F003-GAP-016** | Constructor interactivo de paneles y widgets de KPIs | Tableros predefinidos | **F088** | Construir dashboards React | `TRUE` | Creación, ordenamiento y personalización de widgets métricos por rol de usuario. |

---

## 4. Mandatory Browser Fixes for F004 (Definir organización, sedes y almacenes)

Al iniciar la retro-auditoría de **F004**, las siguientes capacidades de interfaz serán **bloqueantes y obligatorias** para obtener el `USER_ACCEPTANCE = PASS`:

1. **Organizaciones (`/logistics/organizations`):**
   - `LIST`: Tabla interactiva de empresas registradas con estado activo/inactivo.
   - `CREATE`: Modal o formulario para registrar nueva organización con validación de RUC y razón social.
   - `DETAIL`: Vista detallada de la organización seleccionada.
   - `UPDATE`: Modal de edición para actualizar nombre, datos de contacto y estado.
   - `PERSISTENCE`: Confirmación mediante recarga con `F5` de que los cambios persisten en PostgreSQL.
2. **Sedes / Sucursales (`/logistics/branches`):**
   - `LIST`: Tabla de sedes asociadas a cada organización.
   - `CREATE`: Formulario para registrar sedes con dirección, código de establecimiento y tipo.
   - `UPDATE`: Modificación de datos de sede.
   - `DEACTIVATE`: Desactivación de sedes con comprobación de no existencia de almacenes activos dependientes.
3. **Almacenes y Ubicaciones (`/logistics/warehouses`):**
   - `LIST`: Listado de almacenes por sede operativa.
   - `CREATE`: Alta de nuevo almacén con tipo de almacenamiento y responsable.
   - `DETAIL`: Inspección de zonas de almacenamiento y ubicaciones.
   - `UPDATE`: Edición de configuración del almacén.
