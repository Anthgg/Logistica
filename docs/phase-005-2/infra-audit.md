# Auditoría de infraestructura GCP

Auditoría de solo lectura del proyecto `gen-lang-client-0356667380`, 17 de agosto de 2026.

## Inventario documentado frente al real

`docs/deployment/phase_010/infrastructure/01_inventario_gcp.md` describe recursos que en
buena parte no existen. Esto no es un detalle de documentación: cualquier script escrito
contra ese inventario habría fallado.

| Recurso documentado | Estado documentado | Estado real |
|---|---|---|
| Cloud Run API producción `autenticacion-continua-api` | IMPLEMENTADO | **Existe** |
| Cloud Run API staging `proyecto-t1-api-staging` | CONFIGURADO | **No existe** |
| Cloud Run Web prod/staging | CONFIGURADO | **No existen** |
| Artifact Registry `proyecto-t1-images` | CONFIGURADO | **No existe** (el real es `cloud-run-source-deploy`) |
| Secret Manager `DATABASE_URL`, `SECRET_KEY` | CONFIGURADO | **Ningún secreto creado** |
| Service accounts `t1-api-staging-sa`, `t1-api-production-sa` | CONFIGURADO | **No existen** (solo la SA por defecto de Compute) |
| Cloud Run Job `t1-migration-job-*` | — | **No existía; creado por F005.2** |

```
CLOUD_RUN_MIGRATION_JOB_EXISTS = false  → true (creado en F005.2)
STAGING_AVAILABLE               = false
```

## Infraestructura creada por F005.2

| Recurso | Valor |
|---|---|
| Secreto | `DATABASE_URL_PRODUCTION` (versión 1), acceso concedido a la SA del Job |
| Imagen | `.../logistica-migration@sha256:1bce983555e8bcf5c24ecf7d08a862e887344a2188979f3eb95e73c360ce390f` |
| Job | `t1-migration-job-production` · `southamerica-west1` |
| Ejecución | `tasks=1`, `parallelism=1`, `maxRetries=0`, `taskTimeout=1800s`, 1 CPU / 1 GiB |

La imagen se referencia **por digest**, no por etiqueta: una etiqueta se puede mover y
entonces deja de responder a qué código escribió el esquema.

No hay entorno de staging real, así que el pipeline no puede ensayarse allí primero. El
modo `verify-only` cubre parcialmente ese hueco: permite ejercitar autenticación, Job,
conectividad y lectura de revisión sin escribir en la base.

## Hallazgos de seguridad

Ninguno de los dos lo introduce F005.2; los dos son anteriores y siguen vivos.

### 1. `DATABASE_URL` en texto plano en el servicio Cloud Run

Las siete variables de entorno del servicio productivo son literales. Ninguna es una
referencia a Secret Manager. Entre ellas va la cadena de conexión completa a Supabase,
**con la contraseña**.

Consecuencia práctica: cualquiera con permiso de lectura sobre el servicio Cloud Run
—que es un permiso mucho más común que el de leer secretos— obtiene credenciales de
base de datos de producción.

**Recomendación**: rotar la contraseña de Supabase y pasar la variable a Secret Manager.

### 2. `SECRET_KEY` es el valor de ejemplo

El servicio productivo corre con `SECRET_KEY=replace-with-a-secure-random-value`, el
placeholder por defecto. Es la clave con la que se firman cookies y tokens de sesión.

Con una clave de firma conocida, cualquiera puede fabricar sesiones válidas. Es una
vulnerabilidad de autenticación en producción, independiente de esta fase y más urgente
que ella.

**Recomendación**: generar un valor aleatorio, guardarlo en Secret Manager y desplegar.
Rotar la clave invalidará las sesiones activas.

## Estado del resto de workflows

| Workflow | Estado |
|---|---|
| `database-migration.yml` | **Corregido en F005.2** |
| `production-deploy.yml` | Solo `echo`. `INFRA_DEPLOYMENT_PIPELINE=OPEN` |
| `staging-deploy.yml` | Solo `echo`, y con `continue-on-error: true` en auth |
| `cd.yml` | Solo `echo` («Simulated Staging Deployment»), y con `continue-on-error: true` en auth |

F005.2 corrige únicamente el de migraciones, que es su alcance. Los otros tres siguen
siendo simulaciones: conviene no confundir sus ejecuciones en verde con despliegues.

## RLS

`RLS_BASELINE_DRIFT = PRE_EXISTING_INFRA_DEBT`.

Solo las tablas nuevas de F004.5 y F005.1 llevan RLS habilitado por migración. El
centenar largo de tablas heredadas queda como estaba. Reconciliarlas es un trabajo con
su propio análisis de impacto y no pertenece a esta fase.
