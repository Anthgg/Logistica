# Deuda abierta al cierre de F005 / F005.1

Ninguno de estos puntos bloquea el cierre de las fases. Se registran aquí para que
existan como decisión pendiente y no como olvido.

## 1. `LEGACY_ORPHAN_REQUIRES_DATA_DECISION` — almacenes demo huérfanos

Tres almacenes de demostración tenían `organization_id = NULL`. F004 corrigió la causa
—el alta ahora deriva la organización de la sede— y normalizó los datos, pero el origen
de esas filas es material de demo anterior al modelo actual. Qué debe pasar con ellas
(conservar, reasignar, retirar) es una decisión de datos, no técnica.

## 2. `DEV_TEST_FIXTURE_CLEANUP` — bases de datos locales de fase

El PostgreSQL local acumula bases creadas para validar migraciones de cada fase:
`f004_test`, `f004_fresh`, `f004_path`, `f004_chain`, `f0045_clean`, `f0045_from_hj`,
`f005_test`, `f0051_test`, `f0051_clean`, `f0051_step`.

Son locales y desechables. No contienen nada que no se pueda regenerar aplicando las
migraciones. Se conservan mientras las fases sigan en verificación.

## 3. `SESSION_TEST_FLAKE` — intermitencia `401 INVALID_SESSION`

Aproximadamente una aparición por ejecución completa de grupo, en una prueba distinta
cada vez. Localizada en `session_service.py:80-84`: discrepancia entre `sid` y `sub`. No
es caducidad ni revocación.

Clasificación: `OPEN_PRE_EXISTING_TEST_INFRA_DEBT`. Atribución: `UNPROVEN` — se sospechó
de F005.1 y quedó descartado al pasar 2/2 con el mismo conjunto de ficheros.

**No se ha silenciado**: no hay `skip`, ni allowlist, ni assertions relajadas que
acepten `401 OR 409`. Un flake escondido deja de avisar y sigue estando.

## 4. `INFRA_DATABASE_RELEASE_PIPELINE` / `INFRA_DEPLOYMENT_PIPELINE`

Los dos workflows correspondientes son stubs: solo contienen `echo`. No publican
migraciones ni despliegan nada.

- `SUPABASE_PRODUCTION_RELEASE = PENDING_INFRA_AGENT`
- `CLOUD_RUN_PRODUCTION_VERIFICATION = PENDING_INFRA_AGENT`

Ninguna fase ha aplicado migraciones a Supabase productivo ni ha desplegado a Cloud Run.

## 5. Desalineación local de RLS

En la base local hay 383 tablas y solo las nuevas tienen RLS habilitado. Es un desfase
del entorno local respecto a producción, no un cambio introducido por F005.1: la
migración `jl480110048dk` sí habilita RLS en `entity_code_counters`.

## 6. Sockets huérfanos de Docker Desktop (entorno local)

Al cerrar Docker Desktop de forma sucia quedan reparse points colgados que Windows
enumera pero no puede abrir ni borrar, y que impiden el siguiente arranque:

- `%LOCALAPPDATA%\Docker\run\dockerInference`
- `%LOCALAPPDATA%\docker-secrets-engine\engine.sock`

`del`, `Remove-Item` y `fsutil reparsepoint delete` fallan con error 123
(`ERROR_INVALID_NAME`). Lo que sí funciona es **renombrar el directorio padre** y dejar
que Docker recree el socket. Es entorno local, no afecta a CI.
