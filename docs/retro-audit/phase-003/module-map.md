# Mapa de Módulos Logísticos · Fase 003

## 1. Visión General de la Arquitectura Modular

El backend de logística implementa el patrón **Modular Monolith** bajo el namespace `backend/app/modules/logistics/`. El enrutador raíz se monta bajo el prefijo `/api/logistics` a través de `create_logistics_router()` en `app/api/router.py`.

A la fecha de la retro-auditoría, se identifican **24 submódulos** independientes en `app/modules/logistics/` que encapsulan sus propios enrutadores, servicios de aplicación, esquemas de validación (Pydantic) y modelos de persistencia (SQLAlchemy).

Adicionalmente, coexisten **módulos raíz/legacy** montados directamente bajo `/api/*` (como `shipments`, `incidents`, `reports`, `dashboard`) que interactúan con el dominio logístico pero no residen dentro de `app/modules/logistics/`.

---

## 2. Catálogo Detallado de Submódulos Backend (24 Submódulos)

| Submódulo | Dominio F002 | Capas Internas | Archivos | Rutas HTTP | Modelos DB | Servicios Principales | Dependencias Internas | Estado Operacional |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **audit** | Trazabilidad | Event Catalog / Sanitizer | 12 | 5 | 1 | `AuditEventService`, `AuditSanitizer` | *Ninguna* | OPERATIONAL |
| **company_profile** | Almacenes / Maestros | Domain / Application / Persistence | 11 | 29 | 8 | `CompanyProfileService`, `AddressContactService`, `AssetService` | `audit`, `auth_dependencies`, `documents`, `principal` | OPERATIONAL |
| **cost_centers** | Compras | DTO / Models / Router / Service | 5 | 7 | 1 | `CostCenterService` | `auth_dependencies`, `principal`, `procurement` | OPERATIONAL |
| **documents** | Documentos (Transversal) | Domain / Application / Rendering / Series / Codes | 58 | 76 | 21 | `DocumentLifecycleService`, `DocumentVerificationService`, `SeriesService` | `audit`, `auth_dependencies`, `company_profile`, `principal` | OPERATIONAL *(Rendering: BACKEND_ONLY)* |
| **drivers** | Transporte | Domain / Application / Infrastructure | 10 | 20 | 16 | `DriverService`, `CarrierContactPhotoService`, `DocumentRestrictionService` | `audit`, `partners` | OPERATIONAL |
| **files** | Archivos (Transversal) | Domain / Application / Storage / API | 22 | 17 | 15 | `FileStorageService`, `EvidenceService`, `FileHashService` | `audit`, `auth_dependencies`, `principal` | OPERATIONAL |
| **gate_control** | Recepción | Application / Presentation | 11 | 0 *(inbound)* | 3 | `GateControlService`, `VehicleAccessService` | `documents`, `drivers`, `inbound` | OPERATIONAL |
| **inbound** | Recepción | Arrivals, Docks, Receiving, Quarantine, Differences | 234 | 458 | 117 | `ReceivingService`, `DockService`, `ArrivalNoticeService`, `QuarantineService` | `audit`, `auth_dependencies`, `documents`, `drivers`, `files`, `partners`, `principal`, `procurement`, `products`, `rbac`, `units`, `vehicle_verifications`, `vehicles` | OPERATIONAL |
| **integrations** | Integraciones (Transversal) | API / Application | 7 | 1 | 0 | `IntegrationClientService` | `dependencies` | OPERATIONAL |
| **inventory** | Inventario | Ledger / Balances / Putaway | 82 | 104 | 46 | `InventoryLedgerService`, `BalanceQueryService`, `PutawayRuleEngine` | `auth_dependencies`, `documents`, `inbound`, `principal`, `security`, `units` | OPERATIONAL |
| **organization** | Almacenes / Maestros | Service / Repo / Schemas | 6 | 14 | 0 *(usa core)* | `OrganizationService`, `BranchService` | *Ninguna* | OPERATIONAL |
| **partners** | Integraciones / Compras | Domain / Application / Persistence | 10 | 10 | 16 | `PartnerCodeService`, `ComplianceResolver`, `DuplicateDetector` | `audit`, `auth_dependencies`, `principal` | OPERATIONAL |
| **procurement** | Compras | Requisitions, Evaluations, Approvals, Orders | 100 | 52 | 60 | `RequisitionService`, `ApprovalEngine`, `SupplierEvaluationService` | `auth_dependencies`, `cost_centers`, `documents`, `files`, `principal`, `products`, `units` | OPERATIONAL |
| **products** | Inventario / Maestros | Domain / Application / Router | 13 | 17 | 10 | `ProductService`, `CategoryService`, `BrandService`, `CompatibilityEvaluator` | `auth_dependencies`, `principal`, `warehouses` | OPERATIONAL |
| **purchase_orders** | Compras | Router / Service / Schemas / Models | 5 | 7 | 2 | `PurchaseOrderService` | `auth_dependencies`, `partners`, `principal`, `products` | OPERATIONAL |
| **rbac** | Seguridad / Transversal | Catalog / Authorization / Assignments | 19 | 15 | 7 | `RBACAuthorizationService`, `RoleAssignmentService`, `CatalogEngine` | `audit`, `security` | OPERATIONAL |
| **routes_module** | Rutas / Transporte (Transversal) | API / Application | 7 | 1 | 0 | `RouteService` | `dependencies` | OPERATIONAL |
| **ruc** | Integraciones / Maestros | Domain / Application / Presentation | 15 | 11 | 8 | `RucLookupService`, `RucImportService`, `AssistedVerificationService` | `audit`, `auth_dependencies`, `partners`, `principal` | OPERATIONAL |
| **security** | Seguridad / Transversal | Step-Up Policy / Router / Models | 6 | 5 | 2 | `StepUpPolicyService`, `StepUpSessionService` | `auth_dependencies`, `principal` | OPERATIONAL |
| **shared** | Core Compartido | Domain / Application Primitives | 4 | 0 | 0 | `SharedDTOs`, `ValueObjects` | *Ninguna* | OPERATIONAL |
| **units** | Inventario / Maestros | Domain / Conversion Engine / Router | 10 | 10 | 6 | `ConversionEngine`, `DecompositionService`, `ComparisonService` | `auth_dependencies`, `principal`, `products` | OPERATIONAL |
| **vehicle_verifications**| Transporte / Integraciones | Domain / Application / Presentation | 11 | 8 | 10 | `ApplyVerificationService`, `AssistedVerificationService`, `SourceService` | `audit`, `vehicles` | OPERATIONAL |
| **vehicles** | Transporte | Domain / Application / Presentation | 13 | 15 | 13 | `VehicleService`, `CapacityService`, `DocumentService` | `audit`, `auth_dependencies`, `partners`, `principal`, `units` | OPERATIONAL |
| **warehouses** | Almacenes | Domain / Application / QR / Labels | 13 | 27 | 7 | `WarehouseLocationLabelService`, `WarehouseLocationQRService`, `BulkGenerationService` | `audit`, `auth_dependencies`, `documents`, `principal` | OPERATIONAL *(Labels Batch: BACKEND_ONLY)* |

---

## 3. Módulos Relacionados Raíz / Legacy (Fuera de `app/modules/logistics/`)

| Módulo Raíz | Prefijo HTTP | Propósito Logístico Relacionado | Clasificación Arquitectónica | Estado Operacional |
| :--- | :--- | :--- | :--- | :--- |
| **shipments** | `/api/shipments` | Gestión de envíos, tracking de despacho y estados de entrega | `ROOT_API_MODULE` / `LEGACY_ROUTING` | PARTIAL (Integración básica existente) |
| **incidents** | `/api/incidents` | Registro de incidencias operativas y soporte para devoluciones | `ROOT_API_MODULE` / `SHARED_SERVICE` | OPERATIONAL |
| **dashboard** | `/api/dashboard` | Métricas y KPIs de la operación | `ROOT_API_MODULE` / `SHARED_SERVICE` | OPERATIONAL |
| **reports** | `/api/reports` | Generación y exportación de reportes generales | `ROOT_API_MODULE` / `SHARED_SERVICE` | OPERATIONAL |
| **inventory (legacy)**| `/api/inventory` | Endpoints históricos de inventario | `ROOT_API_MODULE` / `LEGACY_COMPATIBILITY` | LEGACY (Coexiste con `/api/logistics/inventory/*`) |
| **warehouses (legacy)**| `/api/warehouses` | Endpoints históricos de almacenes | `ROOT_API_MODULE` / `LEGACY_COMPATIBILITY` | LEGACY (Coexiste con `/api/logistics/warehouses/*`) |
| **routes (legacy)** | `/api/routes` | Endpoints históricos de rutas | `ROOT_API_MODULE` / `LEGACY_COMPATIBILITY` | LEGACY (Coexiste con `/api/logistics/routes/*`) |

---

## 4. Cobertura de Dominios F002

| Dominio F002 | Submódulos Backend Asociados | Módulos Raíz Relacionados | Cobertura de Rutas HTTP |
| :--- | :--- | :--- | :---: |
| **1. Compras** | `procurement`, `purchase_orders`, `cost_centers` | - | 66 rutas |
| **2. Recepción** | `inbound`, `gate_control` | - | 458 rutas |
| **3. Almacenes** | `warehouses`, `organization`, `company_profile` | `warehouses (legacy)` | 70 rutas (+ legacy) |
| **4. Inventario** | `inventory`, `products`, `units` | `inventory (legacy)` | 131 rutas (+ legacy) |
| **5. Trazabilidad** | `audit` | `audit_service` | 5 rutas |
| **6. Salida** | `documents/rendering/outbound_router`, `dispatch_router` | `shipments` | 18 rutas |
| **7. Transporte** | `vehicles`, `vehicle_verifications`, `drivers`, `routes_module` | `routes (legacy)` | 44 rutas (+ legacy) |
| **8. Entrega** | `documents/rendering/delivery_router` | `shipments` | 12 rutas |
| **9. Devoluciones** | `inbound/reception_differences` | `incidents` | 15 rutas |
| **10. Documentos** | `documents` (catalog, series, codes, rendering, packages, verification) | - | 76 rutas |
| **11. KPIs** | - | `dashboard`, `reports` | 10 rutas |
| **12. Integraciones**| `integrations`, `ruc`, `partners` | - | 22 rutas |
