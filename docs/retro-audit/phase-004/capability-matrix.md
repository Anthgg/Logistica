# F004 · Matriz de capacidades

`STATUS`: `INTEGRATED` · `PARTIAL` · `BACKEND_ONLY_JUSTIFIED` · `FRONTEND_MISSING` ·
`CONTRACT_MISMATCH` · `BROKEN` · `NOT_APPLICABLE`.

## Organización

| CAPABILITY | BACKEND_ENDPOINT | METHOD | FRONTEND_ROUTE | COMPONENT | API_CLIENT | UI_ACTION | REQUEST | RESPONSE | AUTH | PERSISTENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Listado | `/api/logistics/organizations` | GET | `/logistics/organizations` | `OrganizationsPage` | `logisticsApi.organizations.list` | tabla + búsqueda + paginación | query | `PaginatedResponse[OrganizationResponse]` | sesión | `logistics_organizations` | **INTEGRATED** |
| Detalle | `/api/logistics/organizations/{id}` | GET | — | — | `logisticsApi.organizations.get` | ninguna | — | `OrganizationResponse` | sesión | idem | **BACKEND_ONLY_JUSTIFIED** (la tabla ya trae todos los campos) |
| Creación | `/api/logistics/organizations` | POST | `/logistics/organizations` | `ResourceDialog` | `...create` | «Nueva organización» | `OrganizationCreate` | 201 | sesión + CSRF | idem | **INTEGRATED** |
| **Edición** | `/api/logistics/organizations/{id}` | PATCH | `/logistics/organizations` | `ResourceDialog` | `...update` | «Editar» | `OrganizationUpdate` | 200 | sesión + CSRF | idem | **PARTIAL** — flujo completo, pendiente de confirmación humana |
| Estado activo/inactivo | `/api/logistics/organizations/{id}/status` | PATCH | `/logistics/organizations` | botón de fila | `...changeStatus` | «Desactivar»/«Activar» | `OrganizationStatusUpdate` | 200 | sesión + CSRF | idem | **BROKEN** — usa `editing?.id ?? org.id`, puede actuar sobre otra fila |

## Sede

| CAPABILITY | BACKEND_ENDPOINT | METHOD | FRONTEND_ROUTE | COMPONENT | API_CLIENT | UI_ACTION | RESPONSE | AUTH | PERSISTENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| Listado por organización | `/api/logistics/organizations/{id}/branches` | GET | `/logistics/branches` | `BranchesPage` | `logisticsApi.organizations.branches` | selector de organización + tabla | `PaginatedResponse[BranchResponse]` | sesión | `logistics_branches` | **INTEGRATED** |
| Detalle | `/api/logistics/branches/{id}` | GET | — | — | `logisticsApi.branches.get` | ninguna | `BranchResponse` | sesión | idem | **BACKEND_ONLY_JUSTIFIED** |
| Creación | `/api/logistics/organizations/{id}/branches` | POST | `/logistics/branches` | botón «Nueva sede» | — | **inerte, sin `onClick`** | 201 | sesión + CSRF | idem | **FRONTEND_MISSING** |
| Edición | `/api/logistics/branches/{id}` | PATCH | — | — | `logisticsApi.branches.update` | ninguna | 200 | sesión + CSRF | idem | **FRONTEND_MISSING** |
| **Desactivación** | `/api/logistics/branches/{id}/status` | PATCH | `/logistics/branches` | botón de fila | `...changeStatus` | «Desactivar»/«Activar» | `BranchResponse` | sesión + CSRF | idem | **PARTIAL** — flujo correcto, pendiente de confirmación humana |
| Relación con organización | FK NOT NULL | — | — | — | — | selector humano | — | — | 114/114 | **INTEGRATED** |

## Almacén

| CAPABILITY | BACKEND_ENDPOINT | METHOD | FRONTEND_ROUTE | COMPONENT | API_CLIENT | UI_ACTION | RESPONSE | AUTH | PERSISTENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| Listado | `/api/logistics/warehouses` | GET | `/logistics/warehouses` | `WarehousesPage` | `warehousesApi.list` | tabla | **`list[WarehouseResponse]`** vs `PaginatedResponse` esperado | permiso `warehouses.read` | `warehouses` | **CONTRACT_MISMATCH + BROKEN** |
| Listado por sede | `/api/logistics/branches/{id}/warehouses` | GET | — | — | `logisticsApi.branches.warehouses` | ninguna | `PaginatedResponse[LogisticsWarehouseResponse]` | sesión | idem | **FRONTEND_MISSING** |
| Detalle | `/api/logistics/warehouses/{id}` | GET | `/logistics/settings/warehouses/{id}` | `WarehouseDetailPage` | `warehousesApi.get` | «Ficha & Estructura» | `WarehouseResponse` | permiso | idem | **BROKEN** — 404 para los 3 almacenes existentes |
| **Creación** | `/api/logistics/branches/{id}/warehouses` · `/api/logistics/warehouses` | POST | — | — | (`logisticsApi.warehouses.create`, sin consumidores) | **ninguna** | 201 | sesión+CSRF / permiso | idem | **FRONTEND_MISSING** |
| Edición | `/api/logistics/warehouses/{id}` | PUT | — | — | `warehousesApi.update` | ninguna | `WarehouseResponse` | permiso | idem | **FRONTEND_MISSING** |
| Edición estructural | — | — | — | — | — | — | — | — | — | **NOT_APPLICABLE** — `LogisticsWarehouseUpdate` y `service.update()` existen pero ninguna ruta los publica |
| Estado activo/inactivo | `/api/logistics/warehouses/{id}/status` | PATCH | — | — | `logisticsApi.warehouses.changeStatus` | ninguna | `LogisticsWarehouseResponse` | sesión + CSRF | `is_active` | **FRONTEND_MISSING** |
| Predeterminado | `/api/logistics/warehouses/{id}/set-default` | POST | — | — | `logisticsApi.warehouses.setDefault` | ninguna | idem | sesión + CSRF | `is_default` | **FRONTEND_MISSING** |
| Relación con organización | FK nullable | — | — | — | — | — | — | — | **0/3 pobladas** | **BROKEN** |
| Relación con sede | FK nullable | — | — | — | — | — | — | — | **0/3 pobladas** | **BROKEN** |

## Owner gaps obligatorios

| Gap | Veredicto | Motivo |
|---|---|---|
| **ORGANIZATION EDIT** | **PASS técnico, pendiente de UAT** | Diálogo completo contra `PATCH /organizations/{id}`; no se ha confirmado en navegador con sesión real |
| **BRANCH DEACTIVATE** | **PASS técnico, pendiente de UAT** | Botón por fila contra `PATCH /branches/{id}/status`, con `row.id` correcto; no confirmado en navegador |
| **WAREHOUSE CREATE** | **FAIL** | No existe UI de creación. Además el listado está roto por dos causas independientes y el almacén nacería sin `organization_id` |

`MANDATORY_AT_OWNER_PHASE = TRUE` para los tres, por lo que F004 no puede cerrarse.

## Regla de selectores

| Formulario | Cumple |
|---|---|
| Sedes — selector de organización | **SÍ** — `<select>` con `{name} ({code})`, envía el UUID |
| Almacenes — selector de organización/sede | **N/A** — no hay formulario que auditar |

Ningún formulario existente pide UUID a mano. La regla se cumple donde hay formulario;
el problema es que falta el formulario de almacén.
