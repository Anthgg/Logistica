# Estado auditado de la base productiva

Auditoría de **solo lectura** realizada el 17 de agosto de 2026 contra la base a la que
apunta el servicio Cloud Run de producción. No se ejecutó ninguna migración.

## Revisión

```
SUPABASE_ALEMBIC_VERSION_BEFORE = hj460110046dk
```

Es decir, producción está en **F004** (organizaciones / sedes / almacenes). Le faltan
dos revisiones:

| Revisión | Fase | Clasificación | Riesgo |
|---|---|---|---|
| `ik470110047dk` | F004.5 UBIGEO | DDL aditivo + DML de siembra + RLS | Bajo |
| `jl480110048dk` | F005.1 contadores | DDL aditivo + DML (3 filas) + RLS | Bajo |

Camino: `hj460110046dk → ik470110047dk → jl480110048dk`. Alembic lo calcula solo; no
hay que saltar ninguna.

## Clasificación detallada

### `ik470110047dk` — F004.5

- **DDL**: crea `geo_departments`, `geo_provinces`, `geo_districts` con sus índices;
  añade la columna **nullable** `ubigeo_code` a `logistics_branches`, con FK
  `ON DELETE SET NULL` e índice.
- **DML**: siembra 25 + 196 + 1893 filas desde `ubigeo_data.json`.
- **RLS**: habilita RLS en las tres tablas nuevas.
- **Destructivo**: no. Ningún `DROP`, `TRUNCATE` ni `DELETE` de datos de negocio.
- **Bloqueo**: el `ALTER TABLE` sobre `logistics_branches` toma un `ACCESS EXCLUSIVE`
  breve. Con 180 filas es despreciable. Añadir una columna nullable no reescribe la
  tabla en PostgreSQL moderno.
- **Downtime**: ninguno esperable.

### `jl480110048dk` — F005.1

- **DDL**: crea `entity_code_counters`.
- **RLS**: la habilita en esa tabla.
- **DML**: inserta 3 filas de contador, inicializadas con `COUNT(*) + 1` de cada tabla.
- **Destructivo**: no.
- **Bloqueo**: solo la tabla nueva.

## Bootstrap de contadores y riesgo de colisión

Medido en producción, en solo lectura:

| Entidad | Filas | Códigos con patrón `PREFIJO######` | Máximo emitido | Bootstrap | Veredicto |
|---|---:|---:|---:|---:|---|
| `organization` | 215 | 0 | — | 216 | Seguro |
| `branch` | 180 | 0 | — | 181 | Seguro |
| `warehouse` | 3 | 0 | — | 4 | Seguro |

`ENTITY_CODE_COLLISION_RISK = NONE`.

El bootstrap por `COUNT(*) + 1` es seguro **en esta base concreta** porque no existe
ni un solo código con la forma que emite F005.1: los códigos actuales son de otra
familia (`ORG-` + hexadecimal). El primer código generado será `ORG000216`, que no
colisiona con nada.

Conviene entender el límite del razonamiento: `COUNT(*) + 1` no es equivalente a
`MAX(secuencia) + 1`. En una base donde ya se hubieran emitido códigos de este formato
y luego se hubieran borrado filas, el contador arrancaría por detrás del máximo. El
verificador comprueba exactamente eso en cada ejecución, en vez de asumirlo.

## Datos de smoke

Los identificadores `ORG000121`, `SED000116` y `ALM000006` creados durante el cierre de
F005.1 son **locales**. Producción tiene 0 códigos con ese patrón, luego no se han
transferido: `PRODUCTION_TEST_DATA_COPIED = FALSE`.

## Conectividad

El host directo de Supabase (`db.<proyecto>.supabase.co`) publica **solo registro
AAAA**: es accesible únicamente por IPv6.

- Cloud Run alcanza la base sin problema — los errores en sus logs son de aplicación
  (`AttributeError`, `TypeError`), no de conexión.
- Un contenedor Docker local **no** la alcanza: `Network is unreachable`. La
  verificación local hay que ejecutarla desde el host, que sí tiene ruta IPv6.

Esto condiciona cualquier herramienta de migración que se pretenda ejecutar desde un
entorno sin IPv6: necesitaría el pooler de Supabase, que tiene otro host y otro formato
de usuario.

## Servicio productivo

| Campo | Valor |
|---|---|
| Servicio | `autenticacion-continua-api` (`southamerica-west1`) |
| `/health` | HTTP 200, `environment=production`, `version=0.9.8` |
| Imagen desplegada | `...:v0.9.8-20260810-2248-final` (10 de agosto de 2026) |
| `RUN_MIGRATIONS` | `false` — el servicio no migra al arrancar |

La imagen desplegada es **anterior a F004.5 y F005.1**: `/api/logistics/catalogs/*`
responde 404 en producción. Migrar la base no despliega el código que la usa; eso
pertenece a `INFRA_DEPLOYMENT_PIPELINE`, que sigue abierto.

## Release ejecutado — 17 de agosto de 2026

| Campo | Valor |
|---|---|
| Job | `t1-migration-job-production` (`southamerica-west1`) |
| Ejecución `verify-only` | `t1-migration-job-production-zqhns` |
| Ejecución `upgrade` | `t1-migration-job-production-x9ktq` |
| Inicio / fin | `03:52:17Z` → `03:53:04Z` (47 s) |
| Resultado | `succeededCount=1`, `failedCount=0` |
| Camino aplicado | `hj460110046dk → ik470110047dk → jl480110048dk` |

```
SUPABASE_ALEMBIC_VERSION_BEFORE = hj460110046dk
SUPABASE_ALEMBIC_VERSION_AFTER  = jl480110048dk
```

Verificación posterior, ejecutada por el propio Job:

| Comprobación | Resultado |
|---|---|
| Tablas F004 / F004.5 / F005.1 | Presentes |
| `geo_departments` / `geo_provinces` / `geo_districts` | 25 / 196 / 1893 |
| RLS en las cuatro tablas nuevas | Habilitado |
| `entity_code_counters` | 3 filas: `organization=216`, `branch=181`, `warehouse=4` |
| Riesgo de colisión | Ninguno |

## Idempotencia

Tercera ejecución, con la base ya en `head`:

```
DATABASE_ALREADY_CURRENT=TRUE
MIGRATION_RESULT=SUCCESS
RESULTADO=PASS
```

Esquema antes y después de esa ejecución: **384 tablas, 6691 columnas** en ambos casos.
Ningún cambio, ningún dato duplicado.

## Datos de smoke, comprobado después de migrar

`logistics_organizations` sigue teniendo **0** códigos con el patrón `ORG######`. Los
identificadores creados en el cierre de F005.1 no llegaron a producción por esta vía.
