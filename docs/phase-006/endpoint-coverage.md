# Cobertura de autorización por endpoint

Generada por `scripts/audit_permission_coverage.py`, que recorre las rutas reales de la
aplicación e inspecciona el árbol de dependencias de cada operación. **No lee OpenAPI**:
el esquema dice qué endpoints existen, no quién los protege.

## Estado tras F006 PR 2

| Clase | Operaciones |
|---|---:|
| Total | **1005** |
| `PERMISSION_PROTECTED` | 885 |
| `AUTH_ONLY` | 59 |
| `ROLE_PROTECTED` | 52 |
| `PUBLIC` | 9 |

```
UNAUTHENTICATED_MUTATING_ENDPOINTS          = 0
AUTH_ONLY_MUTATING_OPERATIONS               = 0   (5 justificadas, ver abajo)
UNJUSTIFIED_UNPROTECTED_SENSITIVE_ENDPOINTS = 0
```

## Por qué 1005 y no 986

OpenAPI declara **986** operaciones. La diferencia son exactamente **19 rutas con
`include_in_schema=False`**, comprobado enumerando el atributo: las 19 ausentes lo
tienen en `False` y las 986 presentes en `True`. Cero rutas al revés.

```
AUTHORIZATION_INVENTORY_OPERATIONS = 1005
OPENAPI_OPERATIONS                 = 986
OPERATION_COUNT_DIFFERENCE         = 19
OPERATION_COUNT_DIFFERENCE_REASON  = include_in_schema=False
COUNT_MODEL_RECONCILED             = TRUE
```

Que una ruta no aparezca en el esquema no la hace inalcanzable. Auditar OpenAPI en vez
de las rutas habría dejado 19 endpoints fuera del análisis — entre ellos asignaciones
de muelle y operaciones de descarga. Por eso el auditor recorre rutas.

## Públicas (9)

Seis son documentación y sondas que FastAPI monta solo (`/openapi.json`, `/docs`,
`/redoc`, …). Las tres declaradas:

| Ruta | Motivo |
|---|---|
| `/live`, `/ready` | Sondas del contenedor; sin ellas Cloud Run no sabe si la instancia vive |
| `/api/i18n/catalog` | Cadenas de interfaz. La pantalla de acceso las necesita antes de que exista sesión |

`UNEXPECTED_PUBLIC_OPERATIONS = 0`.

## Mutaciones con sesión, justificadas (5)

| Operación | Motivo |
|---|---|
| `POST /api/logistics/authorization/check` | Responde si el propio usuario tiene un permiso. Exigir uno para preguntar por los propios es circular |
| `POST /api/logistics/me/context` | Fija el contexto de trabajo propio dentro de ámbitos ya concedidos |
| `POST …/step-up/challenges` | Inicia el desafío que **produce** la prueba reforzada |
| `POST …/challenges/{id}/complete` | Completa el desafío propio, ya atado a la sesión |
| `POST …/challenges/{id}/factors` | Aporta un factor al desafío propio |

Los tres de step-up son el caso del huevo y la gallina: exigir el permiso que la prueba
desbloquea impediría obtenerla nunca.

## Autorizadas por nombre de rol (52)

Quedan 52 operaciones que autorizan con `require_permissions(*roles)`, comparando el
rol de plataforma (`admin`, `supervisor`, `dispatcher`, `warehouse_operator`) en vez de
consultar el catálogo.

**No son un agujero**: deniegan, no conceden. Pero no usan la fuente canónica, así que
un rol logístico no puede alcanzarlas y un cambio en el catálogo no las afecta.

Viven todas en los módulos anteriores al dominio logístico: `/api/clients`,
`/api/incidents`, `/api/inventory`, `/api/reports`, `/api/routes`, `/api/shipments`,
`/api/warehouses`, `/api/research`, `/api/models`, `/api/dashboard`.

Convertirlas toca un subsistema distinto del que cubre F006 y merece su propio análisis
de consumidores. Queda registrado con trinquete: el número no puede subir.

Este recuento apareció al corregir un fallo del propio auditor: comprobaba
`require_permission` antes que `require_permissions`, y como el primero es subcadena del
segundo, los endpoints por rol se tomaban por permisos y acababan contados como «solo
sesión». Por eso informes anteriores decían `ROLE_PROTECTED = 0` y `AUTH_ONLY = 130`.
