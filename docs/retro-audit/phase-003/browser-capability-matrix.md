# Matriz de Capacidades Backend ↔ Frontend, Rutas Reales y Registro de Gaps · Fase 003

## 1. Visión General de la Matriz

Esta matriz consolida la auditoría forense de rutas reales de React (`frontend/src/router/AppRouter.tsx`), contrasta las capacidades del backend (`backend/app/modules/logistics/`) con las superficies de interfaz, incorpora la evidencia empírica de la **Ronda 1 de User Browser Acceptance**, y formaliza los gaps vinculantes asignados a sus fases propietarias en el Plan Maestro (F004 a F100).

---

## 2. Auditoría Forense de Rutas Frontend (AppRouter.tsx vs Documentación)

| Recurso / Dominio | Ruta Anteriormente Documentada | Ruta Real Efectiva en AppRouter | Estado de Carga Real | Diagnóstico / Hallazgo UAT | Fase Propietaria (Owner) |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **Almacenes** | `/logistics/warehouses` | `/logistics/warehouses` | `PAGE_LOAD_PASS` | Carga listado; falta acción de creación de almacén. | **F004** |
| **Productos** | `/logistics/catalog/products` | `/logistics/products` | `PAGE_404` (ruta previa) | La ruta real es `/logistics/products`. | **F023** |
| **Unidades** | `/logistics/catalog/units` | `/logistics/units` | `PAGE_404` (ruta previa) | La ruta real es `/logistics/units`. | **F024** |
| **Órdenes de Compra** | `/logistics/purchasing/orders` | `/logistics/purchasing/purchase-orders` | `PAGE_404` (ruta previa) | La ruta real es `/logistics/purchasing/purchase-orders`. | **F034** |
| **Saldos de Stock** | `/logistics/inventory/balances` | `/logistics/inventory/stock` | `PAGE_404` (ruta previa) | La ruta real es `/logistics/inventory/stock`. | **F045** |
| **Kárdex Ledger** | `/logistics/inventory/ledger` | `/logistics/inventory/ledger` | `PAGE_LOAD_PASS` | Listado y movimientos operativos. | **F044** |
| **Muelles (Docks)** | `/logistics/inbound/docks` | `/logistics/inbound/docks` | `PAGE_LOAD_PASS` | Tablero de operaciones de muelles operativo. | **F038** |
| **Vehículos** | `/logistics/vehicles` | `/logistics/vehicles` | `PARTIAL_UI` | Botón crear restringido; marcas/modelos no integrados. | **F027** |
| **Conductores** | `/logistics/drivers` | `/logistics/drivers` | `PARTIAL_UI` | Consulta de solo lectura; sin CRUD en vista principal. | **F029** |
| **Archivos** | `/logistics/files` | `/logistics/files` | `PARTIAL_UI` | Formulario exige UUIDs y claves técnicas manuales. | **F030** |
| **Centros de Costo** | `/logistics/cost-centers` | `/logistics/catalog/cost-centers` | `PAGE_LOAD_PASS` | Vista interactiva existente; faltan datos semilla para compras. | **F021** |
| **Eventos Auditoría**| `/logistics/audit-events` | `/logistics/audit-events` | `PAGE_500` (corregido) | Error de firma en backend corregido en hotfix F003. | **F007** |
| **Permisos RBAC** | `/logistics/permissions` | `/logistics/permissions` | `PARTIAL_UI` | Muestra códigos técnicos crudos sin traducción humana. | **F006** |

---

## 3. Matriz de Capacidades Funcionales por Dominio

### Dominio 1: Estructura Organizacional, Sedes y Almacenes (F004, F021, F022)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Organizaciones (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/organizations` | `api/company-profile-api.ts` | `/logistics/organizations` | `PARTIAL_UI` | `F003-UAT-GAP-001` → **F004** |
| **Sedes / Branches (CRUD)** | `GET`, `POST`, `PATCH`, `DELETE` | `/api/branches` | `api/company-profile-api.ts` | `/logistics/branches` | `PARTIAL_UI` | `F003-UAT-GAP-002` → **F004** |
| **Almacenes y Zonas (CRUD)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/warehouses` | `api/warehouses-modeling-api.ts` | `/logistics/warehouses` | `MISSING_CREATE` | `F003-UAT-GAP-003` → **F004** |
| **Modelado de Posiciones y Racks** | `GET`, `POST`, `PUT` | `/api/logistics/warehouses/locations` | `api/warehouses-modeling-api.ts` | `/logistics/settings/warehouses/:id` | `PARTIAL_UI` | `F003-UAT-GAP-004` → **F022** |
| **Etiquetas QR en Batch** | `POST (batch)` | `/api/logistics/warehouses/locations/labels/batch` | `api/warehouses-modeling-api.ts` | `/logistics/settings/warehouses/:id` | `PARTIAL_UI` | `F003-UAT-GAP-005` → **F022** |

---

### Dominio 2: Seguridad, Roles, Permisos y Step-Up (F005, F006, F008, F009)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Catálogo de Permisos RBAC** | `GET` | `/api/logistics/rbac/permissions` | `api/logistics-api.ts` | `/logistics/permissions` | `TECHNICAL_LABELS` | `F003-UAT-GAP-006` → **F006** |
| **Gestión de Roles RBAC** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/rbac/roles` | `features/logistics-permissions/api/*` | `/logistics/roles` | `PARTIAL_UI` | `F003-UAT-GAP-007` → **F005** |
| **Asignación de Roles a Usuarios** | `GET`, `POST`, `DELETE` | `/api/logistics/rbac/assignments` | `features/logistics-permissions/api/*` | `/logistics/role-assignments` | `PARTIAL_UI` | `F003-UAT-GAP-008` → **F006** |
| **Autenticación Continua & Step-Up**| `POST`, `GET` | `/api/logistics/security/step-up/*` | `features/continuous-auth/api/*` | Modal Global | `INTEGRATED` | `-` |

---

### Dominio 3: Auditoría y Trazabilidad (F007)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Desglose de Capacidades | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **Visor de Eventos de Auditoría** | `GET` | `/api/logistics/audit-events` | `api/logistics-api.ts` | `/logistics/audit-events` | `PARTIAL` | **LIST:** `INTEGRATED`<br>**HTTP:** `INTEGRATED` (200 OK)<br>**AUTHENTICATION:** `INTEGRATED` (401)<br>**FINE_GRAINED_RBAC:** `NOT_IMPLEMENTED` (403 diferido a F007)<br>**FILTERS:** `MISSING/BROKEN`<br>**ACTION RENDER:** `MISSING/BROKEN`<br>**HUMAN LABELS:** `MISSING`<br>**DETAIL:** `MISSING_IN_UI`<br>**PAGINATION:** `INTEGRATED` | `F003-UAT-GAP-009`, `F003-UAT-GAP-029`, `F003-UAT-GAP-030`, `F003-UAT-GAP-031` → **F007** |
| **Exportación de Logs de Auditoría**| `POST` | `/api/logistics/audit/export` | *Sin cliente específico* | - | `FRONTEND_MISSING` | - | `F003-UAT-GAP-010` → **F007** |

---

### Dominio 4: Custodia de Archivos y Evidencias (F030)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Repositorio Seguro de Archivos** | `GET`, `POST` | `/api/logistics/files` | `api/files-api.ts` | `/logistics/files` | `INTEGRATED` | `-` |
| **Carga Asistida de Evidencias** | `POST (init/chunk/finish)` | `/api/logistics/files/upload-sessions` | `api/files-api.ts` | `/logistics/files/upload` | `MISSING_SELECTORS` | `F003-UAT-GAP-011` → **F030** |
| **Solicitud de Borrado Legal** | `POST`, `GET` | `/api/logistics/files/deletion-requests`| `api/files-api.ts` | `/logistics/file-deletion-requests` | `INTEGRATED` | `-` |

---

### Dominio 5: Motor Documental y Series (F011 - F020)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Catálogo de Familias y Tipos** | `GET` | `/api/logistics/documents/types` | `api/documents-api.ts` | `/logistics/documents` | `INTEGRATED` | `-` |
| **Talonarios y Series Correlativas**| `GET`, `POST`, `PATCH` | `/api/logistics/documents/series`, `/talonarios` | `api/documents-api.ts` | - | `FRONTEND_MISSING` | `F003-UAT-GAP-012` → **F013** |
| **Editor de Plantillas Documentales**| `GET`, `POST`, `PUT` | `/api/logistics/documents/templates` | `api/documents-api.ts` | - | `FRONTEND_MISSING` | `F003-UAT-GAP-013` → **F014** |
| **Generación de Paquetes ZIP** | `POST`, `GET` | `/api/logistics/documents/packages` | `api/documents-api.ts` | Modal en documentos | `PARTIAL_UI` | `F003-UAT-GAP-014` → **F020** |

---

### Dominio 6: Catálogo de Productos y Unidades (F023, F024)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Catálogo de Productos y SKUs** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/products` | `api/products-catalog-api.ts` | `/logistics/products` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-015` → **F023** |
| **Unidades y Conversiones** | `GET`, `POST`, `PUT` | `/api/logistics/units` | `api/units-conversions-api.ts` | `/logistics/units` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-016` → **F024** |
| **Reglas de Compatibilidad SKUs** | `POST`, `GET` | `/api/logistics/products/compatibility`| `api/products-catalog-api.ts` | - | `FRONTEND_MISSING` | `F003-UAT-GAP-017` → **F023** |

---

### Dominio 7: Compras y Requisiciones (F021, F031 - F035)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Centros de Costo (CRUD)** | `GET`, `POST`, `PUT`, `PATCH` | `/api/logistics/cost-centers` | `api/cost-centers-api.ts` | `/logistics/catalog/cost-centers` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-018` → **F021** |
| **Requisiciones de Compra (PR)** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/procurement/requisitions` | `api/purchase-requisitions-api.ts` | `/logistics/purchasing/requisitions` | `MISSING_PREREQUISITE_DATA` | `F003-UAT-GAP-019` → **F031** |
| **Evaluación de Cotizaciones** | `GET`, `POST`, `PUT` | `/api/logistics/procurement/evaluations` | `features/supplier-evaluation/api/*` | `/logistics/purchasing/evaluations` | `PAGE_LOAD_PASS` | `-` |
| **Órdenes de Compra (PO)** | `GET`, `POST`, `PATCH` | `/api/logistics/procurement/purchase-orders` | `api/purchase-orders-api.ts`, `features/purchase-orders/api/*` | `/logistics/purchasing/purchase-orders` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-020` → **F034** |
| **Bandeja de Aprobaciones** | `GET`, `POST (approve/reject)` | `/api/logistics/procurement/approvals` | `features/procurement-approvals/api/*`| `/logistics/purchasing/approvals` | `PAGE_LOAD_PASS` | `-` |

---

### Dominio 8: Recepción, Garita y Calidad (F036 - F043)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Control de Garita y Pesaje** | `GET`, `POST`, `PATCH` | `/api/logistics/inbound/gate-control` | `features/gate-control/api/*` | `/logistics/inbound/gate-control` | `PAGE_LOAD_PASS` | `-` |
| **Gestión de Muelles (Docks)** | `GET`, `POST`, `PUT` | `/api/logistics/inbound/docks` | `features/inbound-docks/api/*` | `/logistics/inbound/docks` | `PAGE_LOAD_PASS` | `-` |
| **Recepción por Escaneo** | `GET`, `POST` | `/api/logistics/inbound/receptions` | `features/inbound-receiving/api/*` | `/logistics/inbound/receiving` | `PAGE_LOAD_PASS` | `-` |
| **Planes de Inspección Calidad** | `GET`, `POST`, `PUT` | `/api/logistics/inbound/quality-plans` | `features/quality-inspection-plans/api/*` | `/logistics/quality/plans` | `PAGE_LOAD_PASS` | `-` |
| **Gestión de Cuarentena** | `GET`, `POST (release/reject)` | `/api/logistics/inbound/quarantine` | `features/quarantine/api/*` | `/logistics/quality/quarantine-zones` | `PAGE_LOAD_PASS` | `-` |
| **Diferencias de Recepción** | `GET`, `POST (resolve)` | `/api/logistics/inbound/differences` | `features/reception-differences/api/*` | `/logistics/inbound/reception-differences` | `PAGE_LOAD_PASS` | `-` |

---

### Dominio 9: Inventario, Kárdex y Balances (F044, F045)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Kárdex y Movimientos Ledger** | `GET`, `POST` | `/api/logistics/inventory/ledger` | `features/inventory-ledger/api/*` | `/logistics/inventory/ledger` | `PAGE_LOAD_PASS` | `-` |
| **Saldos de Stock y Alertas** | `GET` | `/api/logistics/inventory/balances` | `features/inventory-balances/api/*` | `/logistics/inventory/stock` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-021` → **F045** |
| **Motor de Putaway Asistido** | `GET`, `POST (execute)` | `/api/logistics/inventory/putaway` | `features/putaway/api/*` | `/logistics/putaway` | `PAGE_LOAD_PASS` | `-` |

---

### Dominio 10: Maestros de Transporte y Salida (F026, F027, F028, F029, F051, F055, F072)

| Capacidad Backend | Métodos HTTP | Enrutador Backend | Adaptador API Frontend | Ruta Frontend Real | Estado de Integración | Gap ID / Owner Phase |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Maestro de Vehículos** | `GET`, `POST`, `PUT`, `DELETE` | `/api/logistics/vehicles` | `api/vehicles-api.ts` | `/logistics/vehicles` | `PARTIAL_UI` | `F003-UAT-GAP-022` → **F027** |
| **Verificación de Placas** | `GET`, `POST`, `PATCH` | `/api/logistics/vehicle-verifications` | `api/vehicle-verifications-api.ts` | `/logistics/integrations/vehicle-verifications` | `PAGE_LOAD_PASS` | `F003-UAT-GAP-023` → **F028** |
| **Maestro de Conductores** | `GET`, `POST`, `PUT` | `/api/logistics/drivers` | `api/drivers-api.ts` | `/logistics/drivers` | `PARTIAL_UI` | `F003-UAT-GAP-024` → **F029** |
| **Consulta de RUC SUNAT** | `GET`, `POST` | `/api/logistics/ruc` | `api/ruc-integration-api.ts` | `/logistics/ruc` | `PAGE_LOAD_PASS` | `-` |
| **Sincronización Masiva RUC** | `POST` | `/api/logistics/ruc/sync-batch` | *Sin cliente dedicado* | - | `FRONTEND_MISSING` | `F003-UAT-GAP-025` → **F026** |
| **Gestión de Envíos / Shipments** | `GET`, `POST`, `PATCH` | `/api/shipments` | `api/shipment-contracts.ts` | `/shipments` | `PARTIAL_UI` | `F003-UAT-GAP-026` → **F051** |
| **Planificación de Carga** | `POST` | `/api/logistics/documents/rendering/dispatch` | *Sin cliente dedicado* | - | `FRONTEND_MISSING` | `F003-UAT-GAP-027` → **F055** |
| **Prueba de Entrega (POD)** | `POST` | `/api/logistics/documents/rendering/delivery` | *Sin cliente dedicado* | - | `FRONTEND_MISSING` | `F003-UAT-GAP-028` → **F072** |

---

## 4. Inventario Vinculante de Gaps de UAT (Mandatory at Owner Phase)

| GAP_ID | Capacidad Afectada | Estado Actual | OWNER_PHASE | Título Canónico Plan Maestro | MANDATORY_AT_OWNER_PHASE | Requisitos de Prueba en Navegador en Owner Phase |
| :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| **F003-UAT-GAP-001** | Edición de Organizaciones | Modal faltante | **F004** | Definir organización, sedes y almacenes | `TRUE` | `CREATE`, `DETAIL`, `UPDATE` organización, persistencia F5, Network 200. |
| **F003-UAT-GAP-002** | Baja / Desactivación de Sedes | Acción faltante | **F004** | Definir organización, sedes y almacenes | `TRUE` | `CREATE`, `UPDATE`, `DEACTIVATE` sede con integridad referencial. |
| **F003-UAT-GAP-003** | Alta de Almacenes en UI | Botón/modal faltante | **F004** | Definir organización, sedes y almacenes | `TRUE` | Formulario de creación de almacén con selector de sede y responsable. |
| **F003-UAT-GAP-004** | Racks y Posiciones de Almacén | Vista unitaria | **F022** | Modelar almacenes y ubicaciones | `TRUE` | Jerarquía visual de zonas, pasillos y racks. |
| **F003-UAT-GAP-005** | Etiquetas QR en Batch | Generación unitaria | **F022** | Modelar almacenes y ubicaciones | `TRUE` | Selección múltiple e impresión masiva de rotulados QR. |
| **F003-UAT-GAP-006** | Permisos con Etiquetas Humanas | Códigos crudos | **F006** | Definir permisos por acción | `TRUE` | Tabla de permisos con nombres legibles y descripciones en lenguaje natural. |
| **F003-UAT-GAP-007** | Creación Interactiva de Roles | Solo lectura | **F005** | Definir roles logísticos | `TRUE` | Asignación de permisos por matriz interactiva. |
| **F003-UAT-GAP-008** | Asignación Dinámica de Roles | Formulario manual | **F006** | Definir permisos por acción | `TRUE` | Asignación de rol a operador y verificación de permisos en `/logistics/me`. |
| **F003-UAT-GAP-009** | Filtros de Eventos Auditoría | Runtime bug corregido| **F007** | Unificar eventos de auditoría | `TRUE` | Filtrado multi-criterio y visualización de eventos de auditoría sin error 500. |
| **F003-UAT-GAP-010** | Exportación de Logs Auditoría | Sin UI | **F007** | Unificar eventos de auditoría | `TRUE` | Descarga de eventos en formato JSON/CSV. |
| **F003-UAT-GAP-011** | Selector Humano de Recursos File | UUIDs manuales | **F030** | Centralizar archivos y evidencias | `TRUE` | Dropdowns con búsqueda para vincular evidencias a órdenes o vehículos. |
| **F003-UAT-GAP-012** | Mantenimiento de Series y Talonarios| Sin UI | **F013** | Diseñar series y talonarios | `TRUE` | Configuración visual de prefijos, rangos correlativos y alertas de límite. |
| **F003-UAT-GAP-013** | Editor Visual de Plantillas | Sin UI | **F014** | Crear el motor de plantillas | `TRUE` | Vista previa en tiempo real de plantillas PDF. |
| **F003-UAT-GAP-014** | Paquetes Documentales ZIP | Descarga unitaria | **F020** | Implementar descarga, reimpresión y anulación | `TRUE` | Descarga masiva de paquetes documentales de despacho. |
| **F003-UAT-GAP-015** | Matriz de Compatibilidad de SKUs | Sin UI | **F023** | Crear el catálogo de productos | `TRUE` | Configuración de incompatibilidades químicas/físicas de almacenamiento. |
| **F003-UAT-GAP-016** | Simulador de Conversión de Unidades | Vista básica | **F024** | Implementar unidades y conversiones | `TRUE` | Conversión dinámica entre unidades logísticas y comerciales. |
| **F003-UAT-GAP-017** | Mantenimiento de Centros de Costo| Catálogo aislado | **F021** | Configurar datos de la empresa | `TRUE` | Integración fluida de Centros de Costo en formularios dependientes. |
| **F003-UAT-GAP-018** | Pre-requisitos de Requisición | Bloqueo por datos | **F031** | Implementar requerimientos de compra | `TRUE` | Formulario de PR con selectores precargados de centro de costo y productos. |
| **F003-UAT-GAP-019** | Enmiendas de Órdenes de Compra | Sin wizard | **F034** | Implementar órdenes de compra | `TRUE` | Flujo de enmienda de PO con trazabilidad de versiones. |
| **F003-UAT-GAP-020** | Tableros de Saldos de Stock | Sin KPIs dinámicos | **F045** | Calcular saldos de stock | `TRUE` | Visualización en tiempo real de stock disponible, reservado y en cuarentena. |
| **F003-UAT-GAP-021** | Registro Completo de Vehículos | Vista restringida | **F027** | Crear el maestro de vehículos | `TRUE` | Alta de vehículo con marcas/modelos precargados y datos técnicos. |
| **F003-UAT-GAP-022** | Gestión de Licencias de Conductor | Solo lectura | **F029** | Crear el maestro de conductores | `TRUE` | Mantenimiento de categorías MTC y alertas de vencimiento de brevete. |
| **F003-UAT-GAP-029** | Filtros y Búsqueda de Auditoría | Inoperativos en UI | **F007** | Unificar eventos de auditoría | `TRUE` | Búsqueda por texto libre, sincronización de severidades (`info`, `low`, etc.), reseteo de página a 1 y botón de limpiar filtros. |
| **F003-UAT-GAP-030** | Poblado de Acción y Etiquetas | Valor NULL / Códigos crudos | **F007** | Unificar eventos de auditoría | `TRUE` | Poblado de `action` en emisores de eventos y representación en lenguaje natural español. |
| **F003-UAT-GAP-031** | Control Fino de Acceso RBAC en Auditoría | Autenticado pero sin permiso requerido | **F007** (Definición en **F006**) | Unificar eventos de auditoría | `TRUE` | Aplicación de `logistics.audit.read` al endpoint: 200 para usuario con permiso, 403 para usuario sin permiso y 401 para anónimo. |

---

## 5. Contrato de Experiencia de Usuario Humana (Human-Readable UX Contract)

A partir de esta fase, se establecen los siguientes **estándares de usabilidad obligatorios** para todas las pantallas del sistema:

1. **Prohibición de UUIDs y Claves Foráneas Manuales:**
   - Queda estrictamente prohibido que un formulario solicite al usuario escribir manualmente un UUID o un ID numérico interno (`organization_id`, `warehouse_id`, `cost_center_id`, `resource_id`, `supplier_id`).
   - Todos los campos relacionales deben implementarse mediante componentes `Select`, `Combobox` o `Autocomplete` que muestren el nombre/código de negocio de la entidad y envíen el ID de forma transparente.
2. **Traducción Obligatoria de Enums y Códigos Técnicos:**
   - Los códigos de permisos (`logistics.documents.read`) deben mostrarse con etiquetas en español comprensibles ("Ver documentos"). El código técnico solo podrá visualizarse como detalle secundario o tooltip.
   - Los estados de entidades deben mostrarse traducidos: `ACTIVE` → "Activo", `INACTIVE` → "Inactivo", `CANCELLED` → "Anulado", `PENDING_APPROVAL` → "Pendiente de aprobación".
3. **Flujo Autocontenido ante Catálogos Vacíos:**
   - Cuando un selector no encuentre datos (por ejemplo, "Sin centros de costo"), debe mostrar un botón interactivo `+ Crear nuevo centro de costo` o un enlace directo a la vista de creación respectiva.

---

## 6. Estrategia de Datos de Demostración (UAT Demo Data Strategy)

Para evitar bloqueos durante pruebas de usuario:
1. **Aislamiento:** Los datos de UAT/Demo se diferencian de datos de prueba unitaria y producción mediante prefijos identificables (`DEMO-`, `UAT-`).
2. **Idempotencia:** Los scripts de carga de datos semilla deben ser ejecutables múltiples veces sin generar duplicados (`upsert` por código natural).
3. **Gobierno por Fase:** Cada fase propietaria es responsable de proveer su respectivo set de datos semilla para habilitar el UAT de las fases dependientes.
