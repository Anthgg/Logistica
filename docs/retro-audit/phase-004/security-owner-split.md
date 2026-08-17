# F004 · Reparto de propiedad en seguridad

El hueco de autorización encontrado en la auditoría **no** se difiere entero a F006.

## F004 es dueño de

**Enforcement de permisos que ya existen** sobre los endpoints de estructura, y
**aislamiento por organización** sobre Organization / Branch / Warehouse.

Códigos aplicados, todos preexistentes en `permission_catalog.py`:

| Endpoint | Permiso |
|---|---|
| `GET /organizations` | `logistics.organizations.read` |
| `POST /organizations` | `logistics.organizations.create` |
| `GET /organizations/{id}` | `logistics.organizations.read` |
| `PATCH /organizations/{id}` | `logistics.organizations.update` |
| `PATCH /organizations/{id}/status` | `logistics.organizations.change_status` |
| `POST /organizations/{id}/branches` | `logistics.branches.create` |
| `GET /organizations/{id}/branches` | `logistics.branches.read` |
| `GET /branches/{id}` | `logistics.branches.read` |
| `PATCH /branches/{id}` | `logistics.branches.update` |
| `PATCH /branches/{id}/status` | `logistics.branches.change_status` |
| `POST /branches/{id}/warehouses` | `logistics.warehouses.create` |
| `GET /branches/{id}/warehouses` | `logistics.warehouses.read` |
| `GET /branches/{id}/warehouses/{wid}` | `logistics.warehouses.read` |
| `PATCH /warehouses/{id}/status` | `logistics.warehouses.change_status` |
| `POST /warehouses/{id}/set-default` | `logistics.warehouses.set_default` |

**Ningún permiso nuevo.** Ninguna ampliación silenciosa de alcance.

## F006 sigue siendo dueño de

Diseño del catálogo, alta de permisos nuevos, etiquetas humanas, editor de roles
y asignación dinámica. F004 no toca nada de eso.

## Infraestructura reutilizada

`LogisticsPrincipal`, `require_permission(...)`, `can_access_organization(...)`,
`organization_ids`, `is_platform_admin`. No se creó un segundo sistema RBAC.

## Derivación de propiedad

Siempre desde datos persistidos:

```
Warehouse.branch_id -> Branch.organization_id -> principal.can_access_organization(...)
```

Un `organization_id` enviado por el cliente se ignora para decidir permisos. Hay un
test que lo fija: `test_warehouse_create_ignores_client_supplied_organization`.

## Política de step-up que F004 respeta sin tocar

`logistics.organizations.change_status` está catalogado como `critical` con
`requires_step_up = true`. Tener el permiso no basta: sin prueba de verificación
reforzada la respuesta es **403 `STEP_UP_REQUIRED`**.

F004 no relaja esa política. `test_organization_status_change_requires_step_up`
la fija para que nadie la debilite por accidente al pasar por aquí.

Consecuencia para la UAT: el botón Activar/Desactivar de organizaciones mostrará
un error humano («Esta acción requiere verificación adicional de tu identidad»)
mientras no exista el flujo de step-up. Es el comportamiento correcto del sistema,
no un defecto de F004. Desactivar **sedes** sí funciona: ese permiso no exige step-up.

## Alcance vacío frente a alcance global

`allowed_organization_ids` devuelve `None` cuando el principal es administrador de
plataforma o cuando no declara ámbitos. Ese segundo caso replica el contrato que ya
tenía `LogisticsPrincipal.can_access_organization`, que trata la ausencia de ámbitos
como «sin restricción». No es una decisión nueva de F004; cambiarla sería rediseñar
el modelo de alcance, que pertenece a F006.
