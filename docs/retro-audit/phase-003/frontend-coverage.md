# Auditoría Detallada de Cobertura e Integración Frontend ↔ Backend · Fase 003

## 1. Visión General de la Integración Frontend ↔ Backend

El frontend de la aplicación logística (`frontend/src/`) está construido sobre React 18, TypeScript y Vite, organizando su arquitectura en tres niveles de consumo de APIs backend:

1. **API Adapters Globales (`frontend/src/api/`):** 20 clientes tipados basados en el cliente canónico `api-client.ts` (con inyección automática de CSRF token, control de sesión y manejo de Step-Up).
2. **Feature Modules Encapsulados (`frontend/src/features/`):** 16 módulos de dominio que contienen sus propios adaptadores de API especializados, hooks de mutación/consulta, tipos y páginas dedicadas.
3. **Páginas de Enrutamiento (`frontend/src/pages/` y `frontend/src/router/AppRouter.tsx`):** 64 páginas React y más de 85 rutas declaradas en `AppRouter.tsx`.

---

## 2. Matriz Exhaustiva de Cobertura por Submódulo Backend (24 Submódulos + Módulos Raíz)

| Submódulo Backend | Dominio F002 | Rutas Backend | Páginas Frontend Asociadas | Adaptadores de API Frontend | Estado de Integración | Detalle de la Integración y Superficies |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **audit** | Trazabilidad | 5 | `pages/AuditEventsPage.tsx` | `api/logistics-api.ts` | `INTEGRATED_PAGE` | Visualización de eventos de auditoría con filtrado por categoría, severidad, actor y rango temporal. |
| **company_profile** | Almacenes / Maestros | 29 | `pages/CompanyProfileSettingsPage.tsx` | `api/company-profile-api.ts` | `INTEGRATED_PAGE` | Formulario de datos corporativos, sedes, direcciones legales y carga/preview de logotipos oficiales. |
| **cost_centers** | Compras | 7 | `pages/CostCentersPage.tsx` | `api/cost-centers-api.ts` | `INTEGRATED_PAGE` | Mantenimiento de centros de costos, asignación de responsables y límites de aprobación. |
| **documents** | Documentos (Transversal) | 76 | `pages/DocumentsPage.tsx`, visores integrados en modales de compras, recepción y almacén | `api/documents-api.ts`, `features/*/api/*DocumentsApi.ts` | `INTEGRATED_PAGE_AND_BACKEND_ONLY_SURFACES` | Emisión, preview y descarga de PDFs integrada en flujos operativos. La administración masiva de series/talonarios y renderizado dinámico de plantillas es `BACKEND_ONLY`. |
| **drivers** | Transporte | 20 | `pages/DriversPage.tsx`, `pages/DriverDetailPage.tsx`, `pages/DriverLicenseCategoriesPage.tsx`, `pages/DriverAlertsPage.tsx` | `api/drivers-api.ts` | `INTEGRATED_PAGE` | Gestión completa de conductores, licencias MTC, alertas de vencimiento y bloqueo operativo por falta de documentos. |
| **files** | Archivos (Transversal) | 17 | `pages/FilesRepositoryPage.tsx`, `pages/FileUploadPage.tsx`, `pages/FileDetailPage.tsx`, `pages/FileDeletionRequestsPage.tsx` | `api/files-api.ts`, `features/*/api/*EvidenceApi.ts` | `INTEGRATED_PAGE` | Repositorio documental seguro, carga multipart/chunked, cálculo y verificación de hashes SHA-256 y solicitudes de borrado legal. |
| **gate_control** | Recepción | 0 *(inbound)* | `features/gate-control/pages/GateControlDashboardPage.tsx`, `CreateGateCheckInPage.tsx`, `GateCheckInDetailPage.tsx`, `WarehouseGatesSettingsPage.tsx`, `GateVerificationPoliciesPage.tsx` | `features/gate-control/api/gateControlApi.ts`, `gateCheckInsApi.ts`, `warehouseGatesApi.ts` | `INTEGRATED_FEATURE` | Garita de control: registro de check-in vehicular, colas de ingreso a planta, pesaje inicial y políticas de inspección física. |
| **inbound** | Recepción | 458 | 40+ páginas en `features/inbound-docks/`, `features/inbound-receiving/`, `features/quality-inspection-plans/`, `features/quarantine/`, `features/reception-differences/` | 40+ adaptadores en `features/inbound-*` y `features/quality-*` | `INTEGRATED_FEATURE` | Gestión integral de muelles, asignación de turnos, escaneo de bultos, inspección de calidad, cuarentena y resolución de diferencias/mermas. |
| **integrations** | Integraciones (Transversal) | 1 | `pages/RucIntegrationPage.tsx` | `api/ruc-integration-api.ts` | `INTEGRATED_PAGE` | Estado y monitoreo de conectividad con pasarelas y servicios externos (SUNAT). |
| **inventory** | Inventario | 104 | 42 páginas en `features/inventory-balances/`, `features/inventory-ledger/`, `features/putaway/`, `pages/InventoryPage.tsx` | 32 adaptadores API en `inventory-balances`, `inventory-ledger` y `putaway` | `INTEGRATED_FEATURE` | Kárdex contable de movimientos, saldos en tiempo real por ubicación/lote, conciliación y motor de putaway asistido. |
| **organization** | Almacenes / Maestros | 14 | `pages/OrganizationsPage.tsx`, `pages/BranchesPage.tsx` | `api/company-profile-api.ts`, `api/operations-api.ts` | `INTEGRATED_PAGE` | Configuración de estructura multi-empresa, centros de distribución y sedes operativas. |
| **partners** | Integraciones / Compras | 10 | `pages/BusinessPartnersPage.tsx`, `pages/BusinessPartnerDetailPage.tsx`, `features/supplier-evaluation/pages/*` | `api/business-partners-api.ts`, `features/supplier-evaluation/api/*` | `INTEGRATED_PAGE_AND_FEATURE` | Padrón maestro de socios (proveedores, transportistas, clientes) y módulo de evaluación técnica y de cumplimiento. |
| **procurement** | Compras | 52 | `pages/PurchaseRequisitionsPage.tsx`, `PurchaseRequisitionFormPage.tsx`, `PurchaseRequisitionReviewPage.tsx`, `PurchaseRequisitionDetailPage.tsx`, `ApprovalInboxPage.tsx`, `ApprovalPoliciesPage.tsx` | `api/purchase-requisitions-api.ts`, `api/purchase-orders-api.ts`, `features/procurement-approvals/api/*` | `INTEGRATED_FEATURE` | Flujo de abastecimiento: creación de requisiciones, cotizaciones, bandejas de aprobación multinivel y reglas de autorización. |
| **products** | Inventario / Maestros | 17 | `pages/ProductsPage.tsx`, `pages/ProductDetailPage.tsx` | `api/products-catalog-api.ts` | `INTEGRATED_PAGE` | Catálogo de SKUs, familias de productos, marcas, especificaciones técnicas y compatibilidades de almacenamiento. |
| **purchase_orders** | Compras | 7 | `pages/PurchaseOrdersPage.tsx`, `pages/PurchaseOrderDetailPage.tsx`, `features/purchase-orders/pages/*` | `api/purchase-orders-api.ts`, `features/purchase-orders/api/*` | `INTEGRATED_FEATURE` | Emisión, enmiendas, cronogramas de entrega y seguimiento de cumplimiento de órdenes de compra. |
| **rbac** | Seguridad / Transversal | 15 | `pages/RolesPage.tsx`, `pages/PermissionsCatalogPage.tsx`, `pages/RoleAssignmentsPage.tsx` | `api/logistics-api.ts`, `features/logistics-permissions/api/*` | `INTEGRATED_PAGE` | Catálogo de permisos por dominio, asignación de roles a operadores y matriz de control de acceso. |
| **routes_module** | Rutas / Transporte (Transversal) | 1 | `pages/RoutesPage.tsx`, `pages/RouteDetailPage.tsx` | `api/operations-api.ts` | `INTEGRATED_PAGE` | Definición de rutas maestras de transporte, tramos y puntos de parada. |
| **ruc** | Integraciones / Maestros | 11 | `pages/RucIntegrationPage.tsx` | `api/ruc-integration-api.ts` | `INTEGRATED_PAGE` | Consulta en tiempo real al padrón SUNAT con resolución de conflictos de datos y actualización asistida de socios. |
| **security** | Seguridad / Transversal | 5 | `pages/SecurityPage.tsx`, `pages/SessionsPage.tsx`, modales Step-Up en `features/continuous-auth/` | `features/continuous-auth/api/continuousAuthApi.ts`, `api/session-api.ts` | `INTEGRATED_FEATURE` | Autenticación continua, desafíos de seguridad Step-Up para operaciones críticas y visor/revocación de sesiones activas. |
| **shared** | Core Compartido | 0 | - | `api/api-client.ts` | `SHARED_CORE_LIBRARY` | Cliente HTTP base, interceptores de seguridad, tipados compartidos y helpers de error. |
| **units** | Inventario / Maestros | 10 | `pages/UnitsAndConversionsPage.tsx` | `api/units-conversions-api.ts` | `INTEGRATED_PAGE` | Catálogo de unidades de medida, factores de conversión y descomposición dimensional de paquetes. |
| **vehicle_verifications** | Transporte / Integraciones | 8 | `pages/VehicleVerificationsPage.tsx`, `VehicleVerificationRequirementsPage.tsx`, `VehicleVerificationSourcesPage.tsx`, `VehicleVerificationConflictsPage.tsx`, `VehicleVerificationReviewTasksPage.tsx` | `api/vehicle-verifications-api.ts` | `INTEGRATED_PAGE` | Verificación vehicular asistida, auditoría de requisitos técnicos y bandejas de resolución de conflictos. |
| **vehicles** | Transporte | 15 | `pages/VehiclesPage.tsx`, `pages/VehicleDetailPage.tsx`, `pages/VehicleMakesPage.tsx`, `pages/VehicleModelsPage.tsx` | `api/vehicles-api.ts` | `INTEGRATED_PAGE` | Registro de flota de vehículos, capacidades de carga/volumen, control de SOAT y mantenimiento técnico. |
| **warehouses** | Almacenes | 27 | `pages/WarehousesPage.tsx`, `pages/WarehouseDetailPage.tsx` | `api/warehouses-modeling-api.ts` | `INTEGRATED_PAGE_AND_BACKEND_ONLY_SURFACES` | Modelado de almacenes, zonas y posiciones con generación de PDF/QR de ubicaciones. Generación batch es `BACKEND_ONLY`. |
| **shipments (root)** | Salida / Entrega | 18 | `pages/ShipmentsPage.tsx`, `pages/ShipmentDetailPage.tsx` | `api/shipment-contracts.ts` | `PARTIAL_INTEGRATION` | Listado de envíos, tracking de estados y línea de tiempo de eventos. La asignación avanzada de despacho y POD digital en desarrollo. |
| **incidents (root)** | Devoluciones / Soporte | 12 | `pages/IncidentsPage.tsx` | `api/operations-api.ts` | `INTEGRATED_PAGE` | Registro y seguimiento de incidencias operativas y soporte para devoluciones. |
| **dashboard / reports (root)** | KPIs | 10 | `pages/DashboardPage.tsx`, `pages/ReportsPage.tsx` | `api/operations-api.ts` | `INTEGRATED_PAGE` | Dashboard de indicadores operativos, resúmenes de almacén y compras, y exportación de reportes. |

---

## 3. Clasificación y Resumen de Estado de Cobertura

- **INTEGRATED_FEATURE (Módulos de Gran Complejidad con Features Dedicadas):** 8 dominios (`gate_control`, `inbound`, `inventory`, `procurement`, `purchase_orders`, `security/continuous-auth`, `supplier-evaluation`, `putaway`).
- **INTEGRATED_PAGE (Vistas y Formularios Dedicados en Pages):** 14 dominios (`audit`, `company_profile`, `cost_centers`, `drivers`, `files`, `integrations`, `organization`, `partners`, `products`, `rbac`, `routes_module`, `ruc`, `units`, `vehicles`, `vehicle_verifications`, `incidents`, `dashboard/reports`).
- **INTEGRATED_PAGE_AND_BACKEND_ONLY_SURFACES (Páginas Integradas con Superficies Específicas Backend-Only):** 2 dominios (`documents`, `warehouses`).
- **PARTIAL_INTEGRATION (Integración Básica Operativa con Funcionalidades Pendientes):** 1 dominio (`shipments`).
- **SHARED_CORE_LIBRARY (Librería de Soporte):** 1 módulo (`shared`).
- **UNINTEGRATED / ORPHAN PAGES:** `0` (Todas las 64 páginas y 16 features están enlazadas a enrutamiento o componentes de dominio).
