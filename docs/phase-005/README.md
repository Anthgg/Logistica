# Fase 005 — Roles logísticos, matriz de permisos y separación de funciones

Estado: **cerrada**. Backend y frontend en `main`.

F005 no creó un sistema RBAC: el proyecto ya tenía uno (`logistics_roles`,
`logistics_permissions`, `logistics_role_permissions`, `logistics_role_assignments`,
`logistics_role_conflict_rules` y `require_permission`). Lo que faltaba era la
**administración** de ese sistema y el uso real de la tabla de conflictos, que existía
pero estaba vacía.

## Documentos

| Documento | Contenido |
|---|---|
| [`role-matrix.md`](role-matrix.md) | Los 20 roles de sistema y su volumen de permisos |
| [`sod-rules.md`](sod-rules.md) | Reglas de separación de funciones y cómo se evalúan |
| [`legacy-roles.md`](legacy-roles.md) | `ADMIN_LOGISTICA` y `operator`: anomalías congeladas |
| [`custom-roles.md`](custom-roles.md) | Roles personalizados: creación, escalado, auditoría |

## Qué añadió F005

1. **Administración de roles personalizados** (`RoleAdminService`): crear, editar,
   activar/desactivar y reemplazar el conjunto de permisos de roles NO de sistema.
2. **Guarda de escalado de privilegios**: nadie puede otorgar a un rol un permiso que
   él mismo no posee.
3. **Segundo punto de control SoD**: las reglas ya se consultaban al *asignar* un rol a
   un usuario; ahora también al *componer* un rol personalizado.
4. **Vista de matriz** rol × permiso, servida por el backend y renderizada en
   `RolesPage`.
5. **Cinco eventos de auditoría** nuevos: `logistics.role.created`, `.updated`,
   `.activated`, `.deactivated`, `.permissions_updated`.

## Qué NO tocó F005

- Los 20 roles de sistema: ni códigos, ni nombres, ni permisos.
- El catálogo de permisos (`CATALOG_VERSION = 1.2.0`, 524 permisos distintos en matriz).
- `require_permission`, el step-up ni el modelo de scopes.
- Los dos roles heredados anómalos (ver [`legacy-roles.md`](legacy-roles.md)).
- Fase 006: `PHASE_006_IMPLEMENTED=FALSE`.
