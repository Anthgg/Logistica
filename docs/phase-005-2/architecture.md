# Arquitectura del release de base de datos

## Flujo

```
GitHub · workflow_dispatch (manual)
        ↓
GitHub Environment (staging | production)
        ↓
google-github-actions/auth  ← falla en seco si las credenciales no valen
        ↓
gcloud run jobs describe    ← el Job debe existir antes de invocarlo
        ↓
gcloud run jobs execute --wait
        ↓
Cloud Run Job  t1-migration-job-<entorno>
        ↓  DATABASE_URL inyectada desde Secret Manager
        ↓
scripts/run_migration_job.sh
        ├── alembic current            → CURRENT
        ├── alembic heads              → TARGET, HEADS (aborta si HEADS != 1)
        ├── alembic upgrade head
        └── verify_production_schema.py --expected-revision TARGET
        ↓
Supabase PostgreSQL
        ↓
gcloud run jobs executions describe  ← succeededCount / failedCount
```

## Por qué fuera de banda

El `ENTRYPOINT` de la imagen del backend contiene:

```sh
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade heads
fi
```

Es decir: **por defecto, cualquier contenedor de esa imagen migra al arrancar**. En
Cloud Run, donde el servicio escala a varias instancias, eso significa varias
migraciones concurrentes compitiendo por el mismo `alembic_version`.

El servicio productivo ya está configurado con `RUN_MIGRATIONS=false`, así que hoy no
ocurre. Pero el valor seguro depende de que nadie olvide ponerlo. Por eso el Job de
migración **sobreescribe el entrypoint** en vez de reutilizarlo: la migración es una
tarea con principio y fin, no un efecto colateral de arrancar un servidor web.

Nótese además que el entrypoint usa `upgrade heads` (plural), que aplicaría todas las
cabezas si el grafo se bifurcara. El Job usa `upgrade head` (singular) y **aborta** si
detecta más de una: preferimos parar a aplicar una rama que nadie eligió.

## Modos

| Modo | Qué hace | Escribe |
|---|---|---|
| `verify-only` | Conectividad, revisión actual, head objetivo | No |
| `upgrade` | Lo anterior + `alembic upgrade head` + verificación de esquema | Sí |

`verify-only` es el valor por defecto del workflow. Migrar producción exige elegirlo
explícitamente, además del entorno.

## Concurrencia

Tres capas, porque una sola no basta:

1. `concurrency` de GitHub Actions por entorno, sin cancelar la ejecución en vuelo.
2. `parallelism = 1` y `taskCount = 1` en el Cloud Run Job.
3. Alembic toma su propio bloqueo sobre `alembic_version` dentro de la transacción.

## Trazabilidad de imagen

La imagen del Job se etiqueta con el SHA del commit del backend. Sin eso no se puede
responder a la pregunta que importa cuando algo sale mal: *qué código escribió este
esquema*. `latest` no responde a eso.

## Secretos

`DATABASE_URL` la inyecta Secret Manager directamente en el Job. El workflow no la ve,
no la pasa como argumento y no la imprime. La única salida que menciona el destino es
la del verificador, y va enmascarada (`db***.<proyecto>.supabase.co/postgres`).
