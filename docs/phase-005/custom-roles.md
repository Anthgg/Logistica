# Roles personalizados

Fuente canónica: `backend/app/modules/logistics/rbac/role_admin_service.py`.

## Espacio de nombres

`normalize_code` fuerza el prefijo `LOGISTICS_CUSTOM_`. Un rol personalizado nunca puede
colisionar con uno de sistema, aunque el usuario escriba exactamente `LOGISTICS_ADMIN`.

## Guardas al crear o recomponer

Toda creación, edición, cambio de estado y reemplazo de permisos pasa por tres
comprobaciones, en este orden:

1. **`_assert_not_system`** — los 20 roles de `SYSTEM_ROLES` son inmutables desde la
   API. Ver [`role-matrix.md`](role-matrix.md).
2. **`_assert_no_escalation`** — nadie puede otorgar a un rol un permiso que él mismo no
   posee. Sin esta guarda, un administrador limitado podría fabricarse un rol con
   permisos que no tiene y asignárselo: escalada de privilegios en dos pasos.
3. **`_assert_no_sod_conflict`** — el conjunto de permisos resultante no puede reunir
   potestades incompatibles. Ver [`sod-rules.md`](sod-rules.md).

## Auditoría

Cada operación emite un evento del catálogo (`rbac/../audit/catalog.py`):

| Operación | Evento |
|---|---|
| Crear rol | `logistics.role.created` |
| Editar metadatos | `logistics.role.updated` |
| Activar | `logistics.role.activated` |
| Desactivar | `logistics.role.deactivated` |
| Reemplazar permisos | `logistics.role.permissions_updated` |

## Frontend

`src/pages/RolesPage.tsx` pasó de una vista de solo lectura a administración completa +
matriz. El selector de permisos (`src/components/logistics/PermissionSelector.tsx`)
agrupa por dominio, permite buscar y muestra el recuento seleccionado.

Deliberadamente **no** tiene un "seleccionar todo" global: con 524 permisos, un botón
así produce roles que nadie ha revisado y que casi con seguridad disparan SoD o
escalada. La selección masiva existe solo por grupo.
