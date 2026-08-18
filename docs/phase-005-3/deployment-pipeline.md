# Pipeline de despliegue productivo

## Fuente canónica

`production-deploy.yml`. Una sola.

Antes había tres workflows haciendo aproximadamente lo mismo, y los tres simulado:

| Workflow | Estado anterior | Decisión |
|---|---|---|
| `production-deploy.yml` | `echo "Deploying Cloud Run service..."` | **Reescrito**: despliegue real |
| `staging-deploy.yml` | `echo` + `continue-on-error` en auth + disparo por push a `develop` | **Desactivado**: no existe staging |
| `cd.yml` | `echo "Simulated Staging Deployment"` + `continue-on-error` | **Eliminado**: duplicaba a los otros dos |

Tres pipelines para un despliegue garantizan que al menos dos estén desactualizados. El
de staging se deja presente pero desactivado, y falla explicando por qué, en lugar de
fingir un despliegue contra recursos que no existen.

## Flujo

```
workflow_dispatch (commit_sha, promote_traffic)
        ↓
GitHub Environment: production
        ↓
auth GCP  ← sin continue-on-error
        ↓
registrar revisión actual  → destino de rollback
        ↓
Cloud Build → imagen etiquetada con el SHA del commit
        ↓
resolver digest inmutable
        ↓
gcloud run deploy --no-traffic
        ├── --set-secrets  DATABASE_URL, SECRET_KEY
        └── --set-env-vars APP_ENV, COOKIE_SECURE, RUN_MIGRATIONS=false, FRONTEND_URL
        ↓
verificar Ready=True
        ↓
health check
        ↓
promover tráfico 100%
        ↓
verificar /health y /api/logistics/catalogs/countries
        ↓
(si algo falla) → revertir tráfico a la revisión anterior
```

## Decisiones que merecen explicación

**Digest, no etiqueta.** La imagen se etiqueta con el SHA del commit para poder
encontrarla, pero el despliegue usa `imagen@sha256:...`. Una etiqueta se puede mover; un
digest no. Sin eso no se puede responder a la única pregunta que importa durante un
incidente: qué código está sirviendo ahora mismo.

**`--no-traffic` primero.** La revisión nueva se crea sin tráfico, se comprueba que
queda `Ready` y responde al health, y solo entonces recibe el 100%. Una revisión que
arranca no es una revisión que funciona.

**Secretos por referencia.** `--set-secrets` hace que Cloud Run lea de Secret Manager en
tiempo de ejecución. Pasarlos con `--set-env-vars` los dejaría en la línea de comandos:
visibles en los logs del workflow y en el historial de comandos.

**`RUN_MIGRATIONS=false` explícito.** El `ENTRYPOINT` de la imagen migra al arrancar si
esa variable no está puesta —su valor por defecto es `true`—. En Cloud Run, con varias
instancias, eso serían varias migraciones concurrentes. El despliegue la fija en cada
revisión en vez de confiar en que nadie la borre. Las migraciones siguen siendo trabajo
del Job de F005.2.

**Manual, no por push.** El disparador es `workflow_dispatch`. Producción se despliega a
propósito.

## Autenticación GCP

El workflow usa Workload Identity Federation: `workload_identity_provider` y
`service_account` llegan como *variables* de repositorio (no secretos), y el token lo
emite GitHub mediante `id-token: write`. No hay ninguna clave de service account
descargada ni almacenada en GitHub.

Variables de repositorio necesarias:

| Variable | Contenido |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Ruta completa del proveedor de identidad |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | Correo de la service account a suplantar |
| `PRODUCTION_FRONTEND_URL` | Origen del frontend productivo |

Ninguna es secreta: son identificadores de recursos.

## Gates en CI

| Gate | Qué impide |
|---|---|
| 21 guardas del workflow de despliegue | Que vuelva el `echo`, el `continue-on-error`, la etiqueta móvil o el secreto literal |
| 8 pruebas del detector de secretos | Que el detector deje de detectar sin que nadie se entere |
| Guard en shell independiente | Lo mismo, sin depender de pytest |
| Escaneo de secretos sobre workflows y docs de fase | Credenciales productivas versionadas |

Contra el pipeline anterior, 13 de las 21 guardas fallan.

## Rollback

La revisión activa se registra **antes** de desplegar. Si cualquier paso posterior
falla, el tráfico vuelve a ella.

No se revierte la base de datos: el esquema en producción (`jl480110048dk`) es
compatible tanto con la revisión nueva como con la anterior, porque las migraciones de
F004.5 y F005.1 solo añaden. Revertir el esquema destruiría datos sin necesidad.
