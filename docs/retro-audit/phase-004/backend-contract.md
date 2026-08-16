# F004 · Contrato backend real

Baseline OpenAPI: **973 operaciones / 828 paths** (`app.openapi()` sobre el head F004).

## Tres superficies de almacén coexistiendo

El repositorio expone almacenes por tres caminos distintos, con tres contratos distintos:

| # | Módulo | Prefijo | Auth | Notas |
|---|---|---|---|---|
| 1 | `app/modules/logistics/organization` | `/api/logistics` | `require_active_user` | Estructural F004, anidado bajo sede |
| 2 | `app/modules/logistics/warehouses` | `/api/logistics/warehouses` | `require_permission(...)` + `LogisticsPrincipal` | Superficie F022 (ubicaciones, layouts, QR) que además publica CRUD base |
| 3 | `app/api/routes/warehouses` | `/api/warehouses` | `require_permissions(roles)` | Legado, incluye `DELETE` duro |

Ambos módulos logistics montan bajo el mismo router: `warehouses_router` en la línea 145
de `app/modules/logistics/router.py`, `organization_router` en la 184. No colisionan por
`METHOD+PATH`, pero producen pares confusos como
`POST /logistics/warehouses/{id}/status` (query param) y
`PATCH /logistics/warehouses/{id}/status` (cuerpo JSON), que son endpoints diferentes.

## Organización — `app/modules/logistics/organization/api/router.py`

| METHOD | PATH | PROPÓSITO | AUTH | REQUEST | RESPONSE | STATUS |
|---|---|---|---|---|---|---|
| POST | `/api/logistics/organizations` | crear | `require_active_user` + CSRF | `OrganizationCreate` | `OrganizationResponse` | 201 |
| GET | `/api/logistics/organizations` | listar | `get_current_user` | query `page,page_size,search,status` | `PaginatedResponse[OrganizationResponse]` | 200 |
| GET | `/api/logistics/organizations/{id}` | detalle | `get_current_user` | — | `OrganizationResponse` | 200 |
| PATCH | `/api/logistics/organizations/{id}` | **editar** | `require_active_user` + CSRF | `OrganizationUpdate` | `OrganizationResponse` | 200 |
| PATCH | `/api/logistics/organizations/{id}/status` | activar/desactivar | `require_active_user` + CSRF | `OrganizationStatusUpdate` | `OrganizationResponse` | 200 |

`OrganizationResponse` observado en vivo:
`id, code, name, status, country_code, timezone, created_at, updated_at`.

## Sede — mismo router

| METHOD | PATH | PROPÓSITO | AUTH | REQUEST | RESPONSE | STATUS |
|---|---|---|---|---|---|---|
| POST | `/api/logistics/organizations/{org_id}/branches` | crear | `require_active_user` + CSRF | `BranchCreate` | `BranchResponse` | 201 |
| GET | `/api/logistics/organizations/{org_id}/branches` | listar por org | `get_current_user` | query | `PaginatedResponse[BranchResponse]` | 200 |
| GET | `/api/logistics/branches/{id}` | detalle | `get_current_user` | — | `BranchResponse` | 200 |
| PATCH | `/api/logistics/branches/{id}` | editar | `require_active_user` + CSRF | `BranchUpdate` | `BranchResponse` | 200 |
| PATCH | `/api/logistics/branches/{id}/status` | **desactivar** | `require_active_user` + CSRF | `BranchStatusUpdate` | `BranchResponse` | 200 |

`BranchResponse` observado:
`id, organization_id, code, name, status, timezone, address_text, latitude, longitude, created_at, updated_at`.

No hay listado global de sedes: siempre se navega por organización.

## Almacén — módulo organization (estructural)

| METHOD | PATH | PROPÓSITO | AUTH | RESPONSE | STATUS |
|---|---|---|---|---|---|
| POST | `/api/logistics/branches/{branch_id}/warehouses` | **crear** | `require_active_user` + CSRF | `LogisticsWarehouseResponse` | 201 |
| GET | `/api/logistics/branches/{branch_id}/warehouses` | listar por sede | `get_current_user` | `PaginatedResponse[LogisticsWarehouseResponse]` | 200 |
| PATCH | `/api/logistics/warehouses/{id}/status` | activar/desactivar | `require_active_user` + CSRF | `LogisticsWarehouseResponse` | 200 |
| POST | `/api/logistics/warehouses/{id}/set-default` | marcar predeterminado | `require_active_user` + CSRF | `LogisticsWarehouseResponse` | 200 |

**No existe** `GET /logistics/branches/{branch_id}/warehouses/{id}` ni un `PATCH` de
edición en este módulo. El esquema `LogisticsWarehouseUpdate` y
`LogisticsWarehouseService.update()` existen en el código pero **ninguna ruta los expone**.

`LogisticsWarehouseResponse` devuelve `is_active: bool` y **no** devuelve `status` ni
`organization_id`, aunque el `PATCH .../status` recibe `status: "active"|"inactive"`.

## Almacén — módulo warehouses (el que consume el frontend)

| METHOD | PATH | AUTH | RESPONSE |
|---|---|---|---|
| GET | `/api/logistics/warehouses` | `logistics.warehouses.read` | **`list[WarehouseResponse]`** (array desnudo, sin paginar) |
| POST | `/api/logistics/warehouses` | `logistics.warehouses.manage` | `WarehouseResponse` |
| GET | `/api/logistics/warehouses/{id}` | `logistics.warehouses.read` | `WarehouseResponse` |
| PUT | `/api/logistics/warehouses/{id}` | `logistics.warehouses.manage` | `WarehouseResponse` |
| POST | `/api/logistics/warehouses/{id}/status` | `logistics.warehouses.manage` | `WarehouseResponse` (status como **query param**) |

Todos resuelven la organización con `_resolve_org_id(principal)` y filtran
`Warehouse.organization_id == org_id`.

## Autorización y aislamiento

- Sin sesión → **401** `SESSION_REQUIRED`. Verificado en vivo para
  `/api/logistics/organizations` y `/api/logistics/warehouses`.
- El módulo `organization` **no comprueba ningún permiso** y **no filtra por tenant**:
  su única barrera es `require_active_user`. Cualquier usuario activo puede leer y
  modificar cualquier organización, sede o almacén del sistema.
- El módulo `warehouses` sí exige permiso y sí filtra por organización del principal.

Esto es una asimetría real, no una suposición: los permisos
`logistics.organizations.update`, `logistics.branches.change_status`, etc. existen en
`permission_catalog.py` y el frontend condiciona sus botones a ellos, pero el backend
que atiende esas rutas nunca los evalúa.
