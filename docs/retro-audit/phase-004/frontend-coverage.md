# F004 · Cobertura frontend

Worktree: `C:/Users/anthg/LogisticaF-F004` · branch `audit/retro-phase-004-frontend` · `8dcf23b`.

## Rutas registradas

| FRONTEND_ROUTE | PAGE | API CLIENT | BACKEND ENDPOINT |
|---|---|---|---|
| `/logistics/organizations` | `OrganizationsPage` | `logisticsApi.organizations` | módulo organization |
| `/logistics/branches` | `BranchesPage` | `logisticsApi.organizations` / `.branches` | módulo organization |
| `/logistics/warehouses` | `WarehousesPage` | `warehousesApi` (`warehouses-modeling-api`) | módulo warehouses |
| `/logistics/settings/warehouses/{id}` | `WarehouseDetailPage` | `warehousesApi` | módulo warehouses |

`AppRouter.tsx` líneas 277-303.

## OrganizationsPage — 257 líneas

Completa: listado paginado, alta, edición y cambio de estado, todo por diálogo
(`ResourceDialog`) con `isSubmitting`, error controlado y recarga tras éxito.
Los botones se condicionan con `PermissionGate` / `useLogisticsAccess` sobre
`logistics.organizations.{create,update,change_status}`.

**Defecto 1 — fila equivocada al cambiar estado.** `OrganizationsPage.tsx:110`:

```ts
await logisticsApi.organizations.changeStatus(editing?.id ?? org.id, { ... })
```

`editing` conserva la última organización abierta en el diálogo aunque el diálogo se
haya cerrado. Si el usuario edita A, cierra, y luego pulsa Desactivar en la fila B, el
`PATCH` va contra **A**. El cuerpo enviado se calcula además con `org.status` (B), así
que puede llegar a escribir en A el estado invertido de B.

## BranchesPage — 211 líneas

Selector de organización por nombre y código (cumple la regla de selectores), listado
paginado por organización, y acción Desactivar/Activar por fila (esta sí usa `row.id`
correctamente).

**Defecto 2 — botón muerto.** `BranchesPage.tsx:148`:

```tsx
<Button disabled={!selectedOrg}>Nueva sede</Button>
```

Sin `onClick`. El endpoint `POST /organizations/{id}/branches` existe y no hay forma de
alcanzarlo desde el navegador.

**Falta** edición de sede: `PATCH /logistics/branches/{id}` existe en backend y en
`logisticsApi.branches.update`, pero ninguna página lo invoca.

## WarehousesPage — 146 líneas

**Defecto 3 — sin creación.** La página no tiene botón de alta, ni diálogo, ni
`onSubmit`. `PageHeader` se renderiza sin `actions`. El owner gap *warehouse create* no
tiene superficie de navegador: `FRONTEND_MISSING`.

**Defecto 4 — forma de respuesta equivocada.** `warehouses-modeling-api.ts:23` declara
`Promise<PaginatedResponse<Warehouse>>` para `GET /logistics/warehouses`, pero el
backend responde `list[WarehouseResponse]`, un array desnudo. Verificado en vivo:

```
GET /api/logistics/warehouses -> 200
TOP-LEVEL: list
BODY: []
```

Consecuencia exacta (no es un crash): `data.items` queda `undefined`;
`OperationsTable` normaliza con `rows ?? []` y pinta una tabla vacía; `Pagination`
recibe `undefined` y renderiza `Página undefined de NaN · undefined registros`.
Es la misma clase de fallo que el desastre de Documents: el DTO TypeScript decidió por
su cuenta que el backend paginaba.

**Defecto 5 — campos inexistentes.** Las columnas leen `row.branch_name`,
`row.total_locations`, `row.active_locations` y `row.active_layout_version`. Ninguno
existe en `WarehouseResponse`. Se renderizan como `undefined (undefined activas)`.

## DTOs TypeScript vs Pydantic

`src/types/logistics-resources.ts:73`:

```ts
export interface LogisticsWarehouseResponse {
  id, code, name, organization_id: string, branch_id: string,
  status: string, is_default: boolean, created_at, updated_at
}
```

Contra el `LogisticsWarehouseResponse` real del backend:

| Campo | TypeScript | Backend | Veredicto |
|---|---|---|---|
| `organization_id` | `string` | **no se emite** | inventado |
| `branch_id` | `string` | `UUID \| None` | nullable perdido |
| `status` | `string` | **no se emite** (emite `is_active: bool`) | inventado |
| `is_active` | ausente | `bool` | omitido |
| `warehouse_type`, `address`, `district`, `province`, `department`, `capacity` | ausentes | presentes y obligatorios en el request | omitidos |

`LogisticsWarehouseCreate` (TS) manda `{code, name, organization_id, branch_id}`.
El `WarehouseCreate` de backend exige `branch_id` y no conoce `organization_id`; el
`LogisticsWarehouseCreate` del módulo organization exige además `address`, `district`,
`province` y `department`. Ninguna página llama a este cliente, así que el desajuste
todavía no ha producido un fallo visible.

`OrganizationResponse` y `BranchResponse` **sí** coinciden campo a campo con el backend.

## Gates frontend (head F004, sin cambios)

| Gate | Resultado |
|---|---|
| `npm run test` | **622 passed / 93 files**, 0 failed, 0 skipped |
| `npm run typecheck` | **0 errores** |
| `npm run lint` | **0 errores** (solo warnings preexistentes) |
| `npm run build` | **PASS** (9.55 s) |

Los cuatro gates pasan y aun así la pantalla de almacenes está rota. Nada en la suite
cubre `OrganizationsPage`, `BranchesPage` ni `WarehousesPage`: **cobertura cero** para las
tres capacidades de F004.
