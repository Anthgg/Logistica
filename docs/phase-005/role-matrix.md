# Matriz de roles de sistema

Fuente canónica: `backend/app/modules/logistics/rbac/catalog.py` (`SYSTEM_ROLES`) y
`backend/app/modules/logistics/rbac/permission_catalog.py` (`ROLE_PERMISSION_MATRIX`).
Este documento es un reflejo de esos módulos, no una segunda definición: si divergen,
manda el código.

`CATALOG_VERSION = 1.2.0` · 20 roles de sistema · 524 permisos distintos en la matriz.

| Código | Nombre | Permisos |
|---|---|---:|
| `LOGISTICS_ADMIN` | Administrador logístico | 468 |
| `LOGISTICS_MANAGER` | Gerencia logística | 365 |
| `PURCHASING` | Compras | 69 |
| `PURCHASING_APPROVER` | Aprobador de compras | 29 |
| `GATE_CONTROL` | Control de puerta | 18 |
| `RECEIVING` | Recepción | 105 |
| `QUALITY` | Control de calidad | 100 |
| `WAREHOUSE_OPERATOR` | Operador de almacén | 130 |
| `INVENTORY_CONTROLLER` | Control de inventario | 58 |
| `INVENTORY_OPERATOR` | Operador del libro de inventario | 16 |
| `INVENTORY_AUDITOR` | Auditor del libro de inventario | 13 |
| `SYSTEM_INTEGRATION_SERVICE` | Servicio de integración logística | 5 |
| `LEDGER_ADMIN` | Administrador del libro de inventario | 22 |
| `DISPATCH` | Despacho | 21 |
| `TRANSPORT_PLANNER` | Planificador de transporte | 33 |
| `TRANSPORT_MONITOR` | Monitor de transporte | 12 |
| `DRIVER` | Conductor | 13 |
| `DOCUMENT_CONTROLLER` | Control documental | 47 |
| `LOGISTICS_AUDITOR` | Auditor logístico | 130 |
| `LOGISTICS_VIEWER` | Consulta logística | 96 |

## Roles de sistema vs. personalizados

Los 20 de arriba llevan `is_system = true`. `RoleAdminService._assert_not_system` los
protege: cualquier intento de editarlos, cambiarles el estado o reemplazar sus permisos
falla. La razón es que su composición es una premisa del resto del sistema —las pruebas
de permisos, la siembra y los conflictos SoD se declaran sobre esos códigos—.

Los roles personalizados se crean con el prefijo `LOGISTICS_CUSTOM_` (lo impone
`normalize_code`), de modo que el espacio de nombres del sistema no se puede invadir ni
por accidente ni deliberadamente.

## Vista de matriz

`RoleAdminService.matrix` devuelve la relación rol × permiso para pintarla en
`RolesPage`. Es una lectura derivada de `logistics_role_permissions`; no se almacena una
copia.
