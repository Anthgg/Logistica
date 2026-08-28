# Separación de funciones (SoD)

Fuente canónica: `backend/app/modules/logistics/rbac/sod.py`.

## Dos capas de reglas

El proyecto tiene **dos** conjuntos de reglas de conflicto, con propósitos distintos.
Conviene no confundirlos.

### 1. `CONFLICT_RULES` — preexistente, asignación a usuarios

En `rbac/catalog.py`. Gradúa la coexistencia de dos roles **en la misma persona**:

| Rol A | Rol B | Tipo |
|---|---|---|
| `PURCHASING` | `PURCHASING_APPROVER` | `requires_review` |
| `DRIVER` | `TRANSPORT_PLANNER` | `prohibited` |
| `LOGISTICS_AUDITOR` | `WAREHOUSE_OPERATOR` | `prohibited` |
| `LOGISTICS_VIEWER` | `WAREHOUSE_OPERATOR` | `allowed_with_control` |

F005 no las modificó.

### 2. `CANONICAL_SOD_RULES` — añadido por F005, composición de roles

En `rbac/sod.py`. Estas se siembran en `logistics_role_conflict_rules` —la tabla existía
y estaba vacía— y controlan que un **rol personalizado** no reúna dos potestades
incompatibles:

| `rule_code` | Rol A | Rol B | Tipo |
|---|---|---|---|
| `SOD_PURCHASE_ORIGINATE_APPROVE` | `PURCHASING` | `PURCHASING_APPROVER` | `originate_approve` |
| `SOD_RECEIVE_QUALITY_DECIDE` | `RECEIVING` | `QUALITY` | `execute_control` |
| `SOD_INVENTORY_ADJUST_AUDIT` | `INVENTORY_CONTROLLER` | `LOGISTICS_AUDITOR` | `execute_audit` |

Justificación de cada una:

- **Originar / aprobar compra**: quien origina una solicitud o pedido no puede además
  aprobarlo; una sola persona cerraría el ciclo de gasto sin contraparte.
- **Recepcionar / dictaminar calidad**: quien recepciona la mercadería no puede además
  dictaminar su conformidad; el control dejaría de ser independiente de la ejecución.
- **Ajustar / auditar inventario**: quien ajusta inventario no puede auditar esos
  mismos ajustes; revisaría su propio trabajo.

## Cómo se deriva un conflicto de permisos desde una regla de roles

Las reglas se expresan en **roles**, pero un rol personalizado se compone de
**permisos**. La derivación:

```
regla activa (A, B)
    ↓
permisos exclusivos de A  = perms(A) - perms(B)
permisos exclusivos de B  = perms(B) - perms(A)
    ↓
el rol candidato entra en conflicto si toma al menos un permiso
exclusivo de CADA lado
```

El conflicto salta cuando el rol reúne de verdad las dos potestades incompatibles, no
cuando comparte permisos comunes a ambos —que los hay, como leer un almacén—. Por eso
**no** hizo falta una segunda tabla de conflictos a nivel de permiso: las reglas siguen
viviendo donde ya vivían.

## Dónde se evalúa

| Momento | Comprobación |
|---|---|
| Asignar un rol a un usuario | `CONFLICT_RULES` (preexistente) |
| Crear un rol personalizado | `RoleAdminService._assert_no_sod_conflict` |
| Reemplazar los permisos de un rol personalizado | `RoleAdminService._assert_no_sod_conflict` |

Los roles de sistema no se evalúan contra SoD porque no se pueden recomponer; su
composición es un dato de partida.
