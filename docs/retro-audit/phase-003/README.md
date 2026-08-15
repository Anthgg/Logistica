# Fase 003 · Retro-Auditoría: Diseñar la Arquitectura Modular

## 1. Objetivo Oficial

Diseñar la arquitectura modular del sistema logístico, creando el dominio `/api/logistics` y estructurando submódulos independientes bajo el patrón Modular Monolith.

---

## 2. Trabajo Oficial

- Crear el dominio `/api/logistics` y estructurar submódulos independientes.
- Definir como componentes reutilizables: documentos, rutas, archivos, auditoría, integraciones.
- Establecer fronteras de dominio, contratos internos reales y capas internas de aplicación.

---

## 3. Criterio de Cierre Oficial

- Mapa de módulos formalizado y diferenciado.
- Contratos internos reales y matrices de ownership de datos documentados.
- Estructura del repositorio backend y frontend verificada.

---

## 4. Clasificación de la Fase

- **Tipo:** ARCHITECTURE + INFRASTRUCTURE + BACKEND + API_CONTRACT + FRONTEND_ARCHITECTURE
- **Cambios Visuales:** N/A (Fase estrictamente arquitectónica y documental).
- **Impacto en Base de Datos:** N/A (Esquemas existentes operativos).

---

## 5. Baselines Remotos

- **Backend Base SHA:** `6677e2fa9f3875377e9378e43a7160933e5dba4b`
- **Frontend Base SHA:** `699cbfbfc86a7378bac2a4d28fdc3f7285a13564`
- **Rama de Trabajo:** `audit/retro-phase-003-backend`
- **Worktree Aislado:** `Logistica-F003` (directorio de trabajo aislado)

---

## 6. Backend Architecture

El backend adopta una arquitectura de **Modular Monolith** estructurada en `backend/app/modules/logistics/`. Cada submódulo encapsula:
- **Presentation:** Enrutadores FastAPI (`router.py` o `presentation/routes/`).
- **Application:** Servicios de orquestación de casos de uso (`services/` o `application/services/`).
- **Domain:** Entidades de negocio, value objects y reglas de dominio (`domain/` o `models.py`).
- **Infrastructure:** Repositorios, clientes externos y persistencia (`infrastructure/`).

---

## 7. Frontend Architecture

El frontend (`frontend/src/`) se organiza en torno a:
- **Features (`src/features/`):** 16 módulos funcionales encapsulados con sus propios hooks, tipos, componentes y páginas.
- **API Clients (`src/api/`):** 20 clientes adaptadores tipados que consumen el backend a través del cliente canónico `api-client.ts` (con soporte unificado de CSRF, Step-Up y renovación de sesiones).
- **Shared Contexts (`src/contexts/`):** Autenticación (`AuthContext`), verificación continua (`ContinuousAuthProvider`), e internacionalización (`I18nProvider`).
- **Design Primitives (`src/components/ui/`):** Componentes visuales desacoplados de la lógica de negocio.

---

## 8. Montaje del Dominio `/api/logistics` y Conteo Reproducible de Operaciones OpenAPI

- **Enrutador Raíz:** Instanciado mediante `create_logistics_router()` en `app/modules/logistics/router.py`.
- **Punto de Inclusión:** `app/api/router.py` incluye el router con prefijo `/api` + `/logistics` -> `/api/logistics`.
- **Endpoint de Diagnóstico:** `GET /api/logistics/health` reporta estado operacional y versión del dominio.
- **Conteo de Operaciones Registradas en OpenAPI (`app.openapi()`):**
  - **REGISTERED_OPENAPI_PATHS:** `828`
  - **REGISTERED_OPENAPI_OPERATIONS:** `973`
  - **REGISTERED_LOGISTICS_OPERATIONS (`path.startswith('/api/logistics')`):** `894`
  - **REGISTERED_NON_LOGISTICS_OPERATIONS:** `79`
  - **Verificación de Suma:** `894 + 79 = 973` (`SUM MATCH: TRUE`).
- **Métrica de Declaraciones Estáticas (AST):**
  - **STATIC_ROUTE_DECLARATIONS:** `991` (912 en archivos logistics + 79 en api/routes).
  - **Diferencia vs OpenAPI Registrado:** 18 declaraciones estáticas corresponden a enrutadores auxiliares/prototipos no montados en `app` (e.g. `gate_control/presentation/routes.py`).

---

## 9. Inventario de Submódulos (24 Submódulos)

Ver catálogo detallado en [./module-map.md](./module-map.md).
Los 24 submódulos logísticos auditados son:
1. `audit`
2. `company_profile`
3. `cost_centers`
4. `documents`
5. `drivers`
6. `files`
7. `gate_control`
8. `inbound`
9. `integrations`
10. `inventory`
11. `organization`
12. `partners`
13. `procurement`
14. `products`
15. `purchase_orders`
16. `rbac`
17. `routes_module`
18. `ruc`
19. `security`
20. `shared`
21. `units`
22. `vehicle_verifications`
23. `vehicles`
24. `warehouses`

Adicionalmente, coexisten módulos raíz/legacy (`shipments`, `incidents`, `reports`, `dashboard`, `inventory legacy`, `warehouses legacy`, `routes legacy`) montados directamente bajo `/api/*`.

---

## 10. Fronteras de Dominio (Domain Boundaries)

Los 24 submódulos y los módulos raíz mapean a los 12 dominios aprobados en F002:
- **1. Compras:** `procurement`, `purchase_orders`, `cost_centers`
- **2. Recepción:** `inbound`, `gate_control`
- **3. Almacenes:** `warehouses`, `organization`, `company_profile` (+ `warehouses legacy`)
- **4. Inventario:** `inventory`, `products`, `units` (+ `inventory legacy`)
- **5. Trazabilidad:** `audit`
- **6. Salida:** `documents/rendering/outbound_router`, `dispatch_router`, `/api/shipments`
- **7. Transporte:** `vehicles`, `vehicle_verifications`, `drivers`, `routes_module` (+ `routes legacy`)
- **8. Entrega:** `documents/rendering/delivery_router`, `/api/shipments`
- **9. Devoluciones:** `/api/incidents`, `inbound/reception_differences`
- **10. Documentos:** `documents`
- **11. KPIs:** `/api/dashboard`, `/api/reports`
- **12. Integraciones:** `integrations`, `ruc`, `partners`

---

## 11. Servicios Transversales Reutilizables

Se auditaron 5 componentes transversales obligatorios definidos en el Plan Maestro:
1. **Documents:** Motor documental unificado para emisión, plantillas y foliado.
2. **Files:** Custodia segura de binarios y evidencias con cálculo de hash SHA-256.
3. **Audit:** Registro desacoplado de eventos y trazabilidad con sanitización.
4. **Routes:** Cálculo y persistencia de rutas logísticas y manifiestos.
5. **Integraciones:** Gateway desacoplado para servicios externos (padrón RUC SUNAT) con cache local y modo offline.

---

## 12. Documents Architecture

- **Ubicación:** `backend/app/modules/logistics/documents/`
- **Componentes:** Catálogo (`catalog/`), Códigos (`codes/`), Series (`series/`), Renderizado (`rendering/`), Plantillas (`templates/`), Paquetes (`packages/`), Verificación (`verification/`), Histórico (`history/`).
- **Aislamiento:** Expone DTOs y servicios de ciclo de vida (`DocumentLifecycleService`) para que los dominios soliciten emisión sin acoplarse al motor de renderizado HTML/PDF.

---

## 13. Files Architecture

- **Ubicación:** `backend/app/modules/logistics/files/`
- **Componentes:** Storage provider (`storage/`), Metadata repository, Hash calculation (`SHA-256`), Evidence linking.
- **Aislamiento:** Centraliza la subida, custodia y verificación criptográfica de binarios para evitar almacenamiento ad-hoc en dominios de negocio.

---

## 14. Audit Architecture

- **Ubicación:** `backend/app/modules/logistics/audit/` y `app/services/audit_service.py`
- **Componentes:** `AuditService`, `AuditEventCommand`, `AuditContextProvider`, `AuditAction`, `LogisticsAuditEvent`.
- **Aislamiento:** Recibe eventos de contexto, actor, IP, timestamp y payload sanitizado, desacoplando la auditoría de la lógica transaccional. *(La unificación formal de esquemas corresponde a F007)*.

---

## 15. Routes Architecture

- **Ubicación:** `backend/app/modules/logistics/routes_module/` y `app/services/route_service.py`
- **Componentes:** Interfaces de cálculo de distancia, tiempos estimados, waypoints y persistencia de manifiestos. *(La integración de mapas interactivos y GPS corresponde a F061-F070)*.

---

## 16. Integrations Architecture

- **Ubicación:** `backend/app/modules/logistics/integrations/` y `app/modules/logistics/ruc/`
- **Componentes:** Proveedores externos con adaptadores, cache local y modo offline/fallback para evitar que los servicios de negocio llamen directamente a APIs de terceros.

---

## 17. Contratos Internos Reales

Ver especificación detallada en [./internal-contracts.md](./internal-contracts.md).
Los 10 flujos principales inter-dominio se basan en contratos 100% reales en el código:
- **Purchasing → Receiving:** `PurchaseOrderDetailResponse` / `PurchaseOrderModel` (`EXPLICIT_PYDANTIC_SCHEMA` + `PERSISTED_RESOURCE`).
- **Receiving → Inventory:** `InventoryMovementPostingRequestCreate` / `InventoryMovementResponse` / `InventoryMovementModel` (`SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA`; `NO_EXPLICIT_EVENT`).
- **Inventory → Outbound:** `ShipmentCreate` / `Shipment` (`PERSISTED_RESOURCE`).
- **Outbound → Transport:** `VehicleModel` / `DriverModel` (`PERSISTED_RESOURCE`).
- **Transport → Delivery:** `DeliveryPodContext` / `DeliveryPhotoEvidenceSnapshot` / `DeliveryEvidenceValidationSnapshot` / `ReceiverSnapshot` (`EXPLICIT_PYDANTIC_SCHEMA` + `SERVICE_METHOD`).
- **Delivery → Returns:** `IncidentCreate` / `Incident` (`PERSISTED_RESOURCE`).
- **Todos → Documents:** `DocumentLifecycleService.create_draft(...)` / `DocumentLifecycleService.issue_document(...)` / `DocumentCancelRequest` / `DocumentInstanceModel` (`SERVICE_METHOD` + `PERSISTED_RESOURCE`).
- **Todos → Audit:** `AuditContextProvider` / `AuditAction` / `AuditEventCommand` / `AuditService` / `LogisticsAuditEvent` (`SERVICE_METHOD` + `PERSISTED_RESOURCE`).
- **Todos → Files:** `UploadSessionCreateRequest` / `UploadSessionResponse` / `FileAssetModel` / `EvidenceRegisterRequest` / `EvidenceResponse` / `EvidenceRecordModel` (`SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA`).
- **Maestros → Integrations:** `RucLookupService` / `RucLookupResponseSchema` / `ApplyRucDataToPartnerSchema` (`SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA`).

---

## 18. Ownership de Datos

Cada tabla y entidad posee un único dominio responsable de mutaciones y consistencia transaccional (ej: `procurement` es dueño de `purchase_requisitions`, `inventory` es dueño de `inventory_movements`). Los accesos entre dominios se realizan mediante interfaces y DTOs de lectura.

---

## 19. Dirección de Dependencias

- Capa de Presentación (Routers) -> Capa de Aplicación (Services) -> Capa de Dominio (Models/Entities).
- Dominios de Negocio -> Componentes Transversales Compartidos.
- Las dependencias son unidireccionales salvo por los 2 ciclos documentados en la deuda técnica.

---

## 20. Análisis de Ciclos de Dependencia

Ver matriz y evidencia estricta en [./dependency-matrix.md](./dependency-matrix.md).
- **Ciclo 1:** `company_profile` ↔ `documents` (`company_profile/asset_service.py` importa storage de documentos; `documents/application/lifecycle_service.py` importa modelo de perfil; resuelto en runtime vía lazy import).
- **Ciclo 2:** `cost_centers` ↔ `procurement` (`cost_centers/service.py` importa modelo de requisiciones para borrado seguro; `procurement/.../requisition_service.py` importa modelo de centros de costo para validación).

---

## 21. Mapeo Backend ↔ Frontend Grounded

Ver análisis exhaustivo por componente en [./frontend-coverage.md](./frontend-coverage.md).

- **INTEGRATED_FEATURE (8 Dominios con Feature Modules y Sub-Páginas Dedicadas):** `gate_control` (garita), `inbound` (docks, escaneo, cuarentena, inspección, diferencias), `inventory` (balances, ledger, kárdex), `procurement` (requisiciones, aprobaciones), `purchase_orders` (órdenes y enmiendas), `security` (continuous-auth y step-up), `supplier-evaluation` (evaluación de proveedores), `putaway` (almacenamiento asistido).
- **INTEGRATED_PAGE (14 Dominios con Vistas y Formularios en `src/pages/`):** `audit` (`AuditEventsPage`), `company_profile` (`CompanyProfileSettingsPage`), `cost_centers` (`CostCentersPage`), `drivers` (`DriversPage`, `DriverDetailPage`, etc.), `files` (`FilesRepositoryPage`, `FileUploadPage`, etc.), `integrations` (`RucIntegrationPage`), `organization` (`OrganizationsPage`, `BranchesPage`), `partners` (`BusinessPartnersPage`, `BusinessPartnerDetailPage`), `products` (`ProductsPage`, `ProductDetailPage`), `rbac` (`RolesPage`, `PermissionsCatalogPage`), `routes_module` (`RoutesPage`, `RouteDetailPage`), `ruc` (`RucIntegrationPage`), `units` (`UnitsAndConversionsPage`), `vehicles` (`VehiclesPage`, `VehicleDetailPage`), `vehicle_verifications` (`VehicleVerificationsPage`), `incidents` (`IncidentsPage`), `dashboard/reports` (`DashboardPage`, `ReportsPage`).
- **INTEGRATED_PAGE_AND_BACKEND_ONLY_SURFACES (2 Dominios con Superficies Específicas Backend-Only):**
  - `documents`: Visores y descarga de PDFs integrados en modales de negocio; administración general de plantillas y talonarios en batch es `BACKEND_ONLY`.
  - `warehouses`: Modelado de almacenes y ubicaciones integrado; generación masiva de etiquetas QR en batch (`/locations/labels/batch`) es `BACKEND_ONLY`.
- **PARTIAL_INTEGRATION (1 Dominio):** `shipments` (listado y tracking de estados integrados; asignación de despacho avanzada y POD digital en desarrollo).
- **SHARED_CORE_LIBRARY (1 Módulo):** `shared` (`api-client.ts` con manejo de CSRF, autenticación continua y Step-Up).
- **Páginas Frontend Totales Auditadas:** `64` páginas React y `16` features estructuradas.
- **FRONTEND_ONLY / ORPHAN PAGES:** `0`
- **STALE:** `0`
- **UNKNOWN:** `0`

---

## 22. Seguridad Arquitectónica: Uso y Excepciones de LogisticsPrincipal

- **LogisticsPrincipal Canónico:** Inyectado en los submódulos logísticos modernos (`inbound`, `procurement`, `inventory`, `vehicles`, `files`, `rbac`, `security`) para transportar contexto de sesión, roles RBAC y control de acceso.
- **Excepciones Documentadas:**
  - `GET /api/logistics/health`: Utiliza `Depends(get_logistics_current_user)` (sin requerir permisos RBAC específicos).
  - Routers de utilidades y catálogos (`company_profile`, `cost_centers`, `documents/codes`, `documents/rendering`): Utilizan `Depends(get_current_user)` o `Depends(get_db)`.
  - *(La unificación integral de la autenticación y permisos será auditada formalmente en F008 y F009)*.
- **CSRF Protection:** Validación obligatoria en mutaciones HTTP (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Step-Up Authentication:** Políticas de re-autenticación ante operaciones sensibles configuradas en `security/`.

---

## 23. Database Architecture y Conteo de Tablas en PostgreSQL

- **Tablas Base en PostgreSQL (`information_schema.tables`, `table_schema = 'public'`, `table_type = 'BASE TABLE'`):** `339` tablas.
  - Tablas de aplicación creadas por migraciones Alembic activas: `338` tablas.
  - Tabla de control de versionado Alembic: `1` tabla (`alembic_version`).
- **Modelos Declarados en Código SQLAlchemy (`__tablename__`):** `390` modelos declarados (368 en logística + 22 core/compartidos).
- **Exclusiones:** Vistas de base de datos, índices, tablas temporales y modelos base abstractos.

---

## 24. Alembic Impact

- **Estado:** N/A
- **Razón:** La arquitectura modular se encuentra respaldada por las migraciones existentes (33 versiones de migración en `alembic/versions/`). No se requieren cambios en DDL.

---

## 25. Hallazgos (Findings)

- **P0 (Crítico):** 0
- **P1 (Bloqueante):** 0
- **P2 (Acoplamiento Grave):** 0
- **P3 (Deuda Arquitectónica):**
  1. Acoplamiento bidireccional leve `company_profile` ↔ `documents` (resuelto en runtime vía lazy import).
  2. Acoplamiento bidireccional leve `cost_centers` ↔ `procurement` (validación cruzada de integridad antes de borrado).
  3. Coexistencia de endpoints legacy (`/api/shipments`, `/api/inventory`) junto a los endpoints modulares (`/api/logistics/*`).
- **INFO:** Arquitectura modular desacoplada y operativa con 24 submódulos y 973 operaciones OpenAPI registradas.

---

## 26. Correcciones Realizadas

- **Código Productivo:** 0 modificaciones (arquitectura ya operativa).
- **Frontend:** 0 modificaciones.
- **Base de Datos:** 0 modificaciones.
- **Alembic:** 0 modificaciones.
- **Documentación Actualizada y Aterrizada:**
  - `docs/retro-audit/README.md`
  - `docs/retro-audit/phase-003/README.md`
  - `docs/retro-audit/phase-003/module-map.md`
  - `docs/retro-audit/phase-003/internal-contracts.md`
  - `docs/retro-audit/phase-003/repository-structure.md`
  - `docs/retro-audit/phase-003/dependency-matrix.md`

---

## 27. Pruebas de Arquitectura y Regresión

- Análisis estático de importaciones (AST): 24 submódulos verificados y 2 ciclos documentados.
- Validación de OpenAPI: 973 operaciones registradas (894 logísticas y 79 no logísticas).
- Suite de regresión en CI: 100% pruebas de backend, integración PostgreSQL y seguridad superadas.

---

## 28. Integración Continua (CI)

- **PR:** #8 (`audit(phase-003): verify modular logistics architecture`)
- **Pipeline:** Lint (Ruff), Unit Tests, Integration Tests, Security Tests, OpenAPI Verification.

---

## 29. Deuda Técnica Registrada

- Refactorizar en fases posteriores las comprobaciones directas de integridad referencial (`cost_centers` -> `procurement`) hacia un servicio de dominio o DTO anti-corrupción.
- Migrar gradualmente las rutas legacy raíz (`/api/shipments`) hacia `/api/logistics/shipments` preservando compatibilidad.

---

## 30. Evidencia Técnica

- Ejecución de `app.openapi()` confirmando 973 operaciones (894 `/api/logistics/*` + 79 `/api/*`).
- Conteo de base de datos PostgreSQL confirmando 339 tablas base públicas.
- Verificación del montaje en `app/main.py` y `app/api/router.py`.
- Cobertura de los 12 dominios de negocio de F002.

---

## 31. Aceptación de Usuario (User Acceptance)

- **Browser UAT:** `N/A` (Fase estrictamente arquitectónica y documental sin cambios visuales).
- **Architecture Acceptance:** `PENDING_USER_REVIEW` (Sometida a revisión formal del usuario).

---

## 32. Estado Final

```
PHASE_003_READY_FOR_USER_ACCEPTANCE
```
