# Catálogo de permisos

Fuente canónica: **`backend/app/modules/logistics/rbac/permission_catalog.py`**.

No hay una segunda lista. `docs/phase-006/permission_catalog.json` es un artefacto
**derivado**, regenerado por `scripts/audit_permission_catalog.py --export`, y CI falla
si deja de corresponder al módulo. Si alguna vez divergen, es que alguien editó el
artefacto a mano.

## Estado tras F006 PR 2

| Métrica | Valor |
|---|---:|
| Permisos | 555 |
| Códigos duplicados | 0 |
| Referencias a permisos inexistentes | 0 |
| Dominios | 19 |
| Mappings rol–permiso | 1798 |
| Permisos con step-up | 129 (todos con política) |

Riesgo: 215 `low` · 159 `medium` · 145 `high` · 36 `critical`.

## Clasificación de uso

| Estado | Cantidad | Significado |
|---|---:|---|
| `ACTIVE_USED` | 332 | Referenciado desde el código |
| `ACTIVE_ASSIGNED` | 212 | Concedido por algún rol, sin referencia directa |
| `ORPHAN_CANDIDATE` | 11 | Ni referenciado ni concedido |

**Un permiso «usado» no es solo el que aparece en `require_permission`.** Contar solo
esa vía dio 262 huérfanos aparentes en la auditoría inicial; con las cuatro vías reales
—`require_permission`, `require_capability`, `has_permission`, `has_any_permission`—
más las concesiones de la matriz, quedan 11. La diferencia no era deuda: era el
detector mirando por una rendija.

Los 11 candidatos corresponden a funciones que aún no existen (devoluciones, viajes,
prueba de entrega, exportaciones sensibles). **No se borran**: un permiso declarado sin
implementación es una intención registrada, y borrarlo pierde esa información sin
ganar nada.

## Cómo añadir un permiso

Toda entrada nueva necesita las siete claves obligatorias:

```python
{
    "code": "logistics.<recurso>.<accion>",
    "resource": "<recurso>",
    "action": "<accion>",
    "name": "<nombre humano>",
    "description": "<qué autoriza, en una frase>",
    "category": "<uno de los 19 dominios existentes>",
    "risk_level": RiskLevel.MEDIUM,
}
```

Opcionales: `is_sensitive`, `requires_reason`, `requires_step_up`.

Después:

1. concédelo en `ROLE_PERMISSION_MATRIX` a los roles que lo necesiten, con mínimo
   privilegio — la matriz solo puede conceder permisos que existan;
2. si lleva `requires_step_up`, la política se sintetiza sola (ver
   [`permission-risk.md`](permission-risk.md));
3. regenera el artefacto derivado;
4. añade la prueba 401/403/éxito del endpoint que lo exige.

## Códigos: inmutables

El `code` es el identificador estable que usan la base, el código y el frontend.
**No se renombra.** Para un cambio semántico: permiso nuevo, deprecación del anterior
y un periodo de compatibilidad. Renombrar en silencio rompe asignaciones existentes sin
que nada lo indique.
