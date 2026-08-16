# Registro de Aceptación de Usuario · Ronda 3 · Fase 003

## 1. Resumen Ejecutivo

- **Fase Auditada:** F003 · Diseñar la arquitectura modular
- **Ronda de Evaluación:** Ronda 3 (User Browser Acceptance)
- **Superficie Evaluada:** `/logistics/audit-events` (Visualización de eventos y navegación)
- **Evidencia Empírica del Usuario en Navegador:**
  - **Page Load:** `PASS` (Carga fluida de la vista)
  - **Endpoint HTTP:** `GET /api/logistics/audit-events?page=1&page_size=20` → `HTTP 200 OK`
  - **Data Render:** `PASS` (516 eventos visibles y paginados en tabla)
  - **HTTP 500:** `NO` (Error 500 completamente erradicado)
  - **React Crashes / White Screen:** `NO` (Consola limpia de excepciones bloqueantes)
- **Defectos Funcionales Detectados en Ronda 3:**
  1. **Filtros Inoperativos (`FILTERING = FAIL`):** La caja de búsqueda y el selector de severidad no filtran la información en la base de datos ni interactúan adecuadamente con el contrato del backend.
  2. **Columna Acción Vacía (`ACTION_RENDERING = FAIL`):** La columna "Acción" muestra `—` en todas las filas debido a que los eventos se generan sin poblar el campo `action` en la base de datos.
- **Dictamen Arquitectónico:**
  - **Superficie Arquitectónica F003:** `PASS` (La ruta existe, el contrato modular responde, la tabla renderiza y la infraestructura de permisos y datos opera sin caídas).
  - **Completitud Funcional de Auditoría:** `PARTIAL` (Diferida formalmente a su fase propietaria **F007: Unificar eventos de auditoría**).
- **Estado de Aceptación de Usuario:** `PENDING_USER_DECISION` (Sometido a decisión formal del usuario humano).
- **Merge a Main:** `NOT AUTHORIZED`
- **Fase 004:** `BLOCKED`

---

## 2. Auditoría Forense de los Defectos Funcionales Detectados

### 2.1. Auditoría de Filtros (`AuditEventsPage.tsx` ↔ `router.py` ↔ `service.py`)

| Control de Interfaz | Variable de Estado React | Parámetro Enviado por API Client | Parámetro Aceptado en Backend Router | Estado del Filtro | Causa Raíz |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Caja de Búsqueda** ("Nombre, código o documento...") | `search` | `?search=<valor>` | *No declarado en router* | `FAIL` (Inoperativo) | `FRONTEND_CAPABILITY_WITHOUT_BACKEND_SUPPORT`: El frontend envía `search`, pero `router.py` y `AuditService.list()` no declaran ni procesan búsqueda de texto libre. |
| **Selector de Severidad** ("Todas las severidades") | `severityFilter` | `?severity=<valor>` | `severity: str \| None` | `FAIL` (Desalineación de Enums) | `ENUM_MISMATCH`: El dropdown ofrece `low`, `medium`, `high`, `critical`. Sin embargo, todos los 516 eventos en la BD fueron registrados con `severity = 'info'`, valor que no existe en el dropdown del frontend. |
| **Filtro por Categoría** | *Sin control UI* | - | `category: str \| None` | `MISSING_UI` | Backend soporta filtrado por `category`, pero la vista no expone el selector. |
| **Filtro por Actor / Usuario** | *Sin control UI* | - | `actor_user_id: UUID` | `MISSING_UI` | Backend soporta `actor_user_id`, pero no hay combobox en la interfaz. |
| **Filtro por Recurso** | *Sin control UI* | - | `resource_type: str` | `MISSING_UI` | Backend soporta `resource_type`, sin selector en UI. |
| **Paginación** | `page` | `?page=X&page_size=20` | `page: int, page_size: int` | `PASS` (Operativo) | Paginación funciona fluidamente en frontend y backend (26 páginas). |

---

### 2.2. Trazabilidad de Datos de la Columna "Acción"

| Capa del Sistema | Campo / Expresión | Valor Real Observado en Runtime | Diagnóstico Forense |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `logistics_audit_events.action` | `NULL` (516 filas de 516 son `NULL`) | `EVENT_GENERATION_DATA_GAP`: Los emisores de eventos llaman a `audit_service.write_event(...)` especificando `event_code`, pero omiten el argumento `action`. |
| **SQLAlchemy ORM** | `LogisticsAuditEvent.action` | `None` | El modelo mapea la columna como `Mapped[str | None]`. |
| **FastAPI / Pydantic** | `AuditEventSummaryResponse.action` | `null` | El esquema declara `action: str | None` y serializa `null`. |
| **JSON Response** | `"action"` | `null` | Payload HTTP contiene `"action": null`. |
| **TypeScript DTO** | `AuditEventSummaryResponse.action` | `string | null` | Tipado consistente. |
| **React Component** | `row.action ?? '—'` | `'—'` | El operador nullish coalescing renderiza el fallback `'—'`. |

- **Conclusión:** No es un bug de serialización ni de renderizado en React. La causa raíz es un **gap de generación de datos y diseño contractual**: la acción de negocio se codificó únicamente dentro del identificador jerárquico `event_code` (ej. `logistics.document.cancelled`), dejando el campo `action` sin poblar y sin una capa de traducción a español legible para humanos.

---

### 2.3. Auditoría de Seguridad y Control de Acceso (RBAC)

| Verificación de Seguridad | Resultado Real | Diagnóstico / Estado |
| :--- | :---: | :--- |
| **Petición Anónima (Sin sesión)** | `401 Unauthorized` | `PASS` (FastAPI `get_current_user` rechaza requests sin cookie de sesión válida). |
| **Usuario Autenticado con Permiso** | `200 OK` | `PASS` (Usuarios autenticados con rol administrativo/operativo reciben datos). |
| **Usuario Autenticado Sin Permiso (`logistics.audit.read`)** | `200 OK` (Debería ser `403`) | `AUTHENTICATED_BUT_PERMISSION_NOT_ENFORCED`: El endpoint `list_audit_events` en `router.py` declara `user: User = Depends(get_current_user)`, pero aún no declara `principal: LogisticsPrincipal = Depends(require_permission("logistics.audit.read"))`. La aplicación de autorización fina por acción se encuentra diferida a la fase propietaria **F007**. |
| **Prueba de Mutación RBAC 403** | `N/A` | `NOT_APPLICABLE_UNTIL_OWNER_PHASE` (No aplica hasta la implementación del enforcement en F007). |

---

## 3. Asignación de Gaps Obligatorios a Fase Propietaria (Owner: F007)

De acuerdo con la regla de retro-auditoría, estos defectos funcionales **no deben ser implementados prematuramente en F003**, sino asignados formalmente a **F007 (Unificar eventos de auditoría)** con carácter de obligatoriedad:

1. **`F003-UAT-GAP-029` · Audit Events Filters & Search Contract Alignment (Owner: F007):**
   - Implementación de búsqueda por texto libre (`search`) en backend (`event_code`, `actor_display_name_snapshot`, `resource_id`, `reason_text`).
   - Sincronización del catálogo de severidades en UI (`info`, `low`, `medium`, `high`, `critical`).
   - Incorporación de selectores por categoría, actor y tipo de recurso.
   - Reseteo automático de paginación a `page = 1` al modificar cualquier filtro.
   - Botón de "Limpiar filtros" y estado vacío amigable ("No se encontraron eventos con los criterios seleccionados").

2. **`F003-UAT-GAP-030` · Audit Events Action Field & Human-Readable Labels (Owner: F007):**
   - Poblado obligatorio del campo `action` en todos los emisores de eventos del sistema.
   - Mapeo y traducción a lenguaje natural en español:
     - `logistics.document.cancelled` → "Documento anulado" / Acción: "Anular documento"
     - `logistics.document.draft_created` → "Borrador creado" / Acción: "Crear borrador"
     - `logistics.document.issued` → "Documento emitido" / Acción: "Emitir documento"
   - Presentación de códigos técnicos (`event_code`) únicamente como metadato secundario o detalle colapsable.

3. **`F003-UAT-GAP-031` · Audit Events Fine-Grained RBAC Enforcement (Owner: F007 / Definición: F006):**
   - Aplicación de `require_permission("logistics.audit.read")` al enrutador de auditoría.
   - Retorno estricto de `HTTP 403 Forbidden` para usuarios autenticados sin el permiso requerido.
   - Ocultamiento de la pestaña o bloqueo transparente en la interfaz de usuario.

---

## 4. Requisitos Obligatorios de Prueba en Navegador para F007

En la fase F007, el gate de aceptación en navegador deberá ejecutar y aprobar:

1. `LIST`: Carga de eventos con datos completos y legibles.
2. `SEARCH`: Búsqueda de eventos por texto libre devolviendo coincidencias exactas y parciales.
3. `CATEGORY_FILTER`: Filtrado por categoría documental, inventario, garita, etc.
4. `SEVERITY_FILTER`: Filtrado por severidad (`info`, `low`, `medium`, `high`, `critical`).
5. `RESULT_FILTER`: Filtrado por resultado (`success`, `failure`).
6. `RESOURCE_FILTER`: Filtrado por tipo de recurso.
7. `ACTION_COLUMN`: Visualización de acciones en lenguaje natural (0 celdas con `—` injustificado).
8. `EMPTY_FILTER_STATE`: Mensaje descriptivo ante 0 coincidencias (sin 500, sin 404, sin spinner infinito).
9. `CLEAR_FILTERS`: Restauración de listado completo y página 1.
10. `EVENT_DETAIL_MODAL`: Inspección de cambios (`previous_data`, `new_data`, `changed_fields`, `metadata`).
11. `RBAC_AUTHORIZED`: Retorna HTTP 200 para rol con `logistics.audit.read`.
12. `RBAC_UNAUTHORIZED`: Retorna HTTP 403 para rol sin permiso.
13. `F5_PERSISTENCE`: Persistencia de filtros y sesión tras recarga.
14. `CONSOLE_AND_NETWORK`: 0 errores no controlados.

---

## 5. Dictamen Final de Ronda 3

```
FASE: F003 · Diseñar la arquitectura modular
SUPERFICIE ARQUITECTÓNICA: PASS (Rutas, API, DB y componentes conectados)
MÓDULO DE AUDITORÍA: PARTIAL (Filtros y etiquetas humanas diferidos a F007)
USER_ACCEPTANCE: PENDING_USER_DECISION
MERGE: NOT AUTHORIZED
F004: BLOCKED
```
