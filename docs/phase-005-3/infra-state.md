# Estado de infraestructura

## Cloud Run — antes y después

| Campo | Antes | Después |
|---|---|---|
| Revisión con tráfico | `...-v0-9-8-final-20260810` | `...-sha-c4363ea2580d` |
| Imagen | etiqueta `v0.9.8-20260810-2248-final` | referencia por digest |
| Digest | `sha256:faf6c34f...` | `sha256:bbeb1bb4...` |
| Origen | sin trazabilidad a un commit | `main` en `c4363ea2580df7cf4f3a4390e42c2fc1d386d445` |
| `DATABASE_URL` | valor literal, con contraseña | referencia a Secret Manager |
| `SECRET_KEY` | valor literal, el de ejemplo | referencia a Secret Manager |
| `RUN_MIGRATIONS` | `false` | `false`, fijado por el despliegue |
| Catálogos F005.1 | HTTP 404 | HTTP 401 (existen y exigen sesión) |

Servicio `autenticacion-continua-api` · proyecto `gen-lang-client-0356667380` · región
`southamerica-west1`.

## Variables de entorno de la revisión activa

| Variable | Origen |
|---|---|
| `DATABASE_URL` | Secret Manager |
| `SECRET_KEY` | Secret Manager |
| `APP_ENV`, `COOKIE_SECURE`, `RUN_MIGRATIONS`, `FRONTEND_URL` | Valor literal |

Los cuatro literales son configuración, no secretos. Tratar cada cadena como secreto
diluye la categoría y complica el despliegue sin ganar nada.

`FRONTEND_URL` conserva el valor que ya tenía producción: es el origen que autoriza CORS
(`app/main.py:100`), y cambiarlo habría roto al frontend actual.

## Secret Manager

| Secreto | Creado en | Contenido |
|---|---|---|
| `DATABASE_URL_PRODUCTION` | F005.2 | Cadena de conexión productiva |
| `SECRET_KEY_PRODUCTION` | F005.3 | Clave de firma JWT, `token_urlsafe(48)` |

Ambos con acceso concedido a la service account de ejecución, solo con
`roles/secretmanager.secretAccessor`.

## Identidad para GitHub Actions

Workload Identity Federation, sin ninguna clave descargada:

| Recurso | Valor |
|---|---|
| Pool | `github` (global) |
| Proveedor | `github-anthgg`, emisor `token.actions.githubusercontent.com` |
| Condición | `assertion.repository_owner == 'Anthgg'` |
| Vinculación | `roles/iam.workloadIdentityUser` acotado a `attribute.repository/Anthgg/Logistica` |

Antes de F005.3 **no existía ningún secreto de GitHub**: los workflows referenciaban
`GCP_SA_KEY_MIGRATIONS` y `GCP_SA_KEY_STAGING`, que nunca se crearon. Cualquier
ejecución habría fallado en autenticación — y con `continue-on-error: true` habría
seguido igualmente hasta terminar en verde.

Las tres variables de repositorio (`GCP_WORKLOAD_IDENTITY_PROVIDER`,
`GCP_DEPLOY_SERVICE_ACCOUNT`, `PRODUCTION_FRONTEND_URL`) son identificadores, no
secretos.

## Deuda documentada

**Service account con permisos amplios.** La cuenta de ejecución es la de Compute por
defecto y tiene `roles/editor` además de `run.admin`, `artifactregistry.writer`,
`logging.logWriter` e `iam.serviceAccountUser`. `roles/editor` excede lo necesario.
Corregirlo obliga a repartir permisos entre una cuenta de ejecución y otra de
despliegue, y a comprobar qué más depende hoy de esa cuenta; se deja registrado en vez
de tocarlo dentro de esta fase.

**`PRODUCTION_ENVIRONMENT_PROTECTION=PENDING`.** El workflow usa el environment
`production`, pero en el repositorio solo existe `copilot`. Sin el environment creado no
hay revisores obligatorios: el gate de aprobación está declarado, no aplicado.

**`STAGING_AVAILABLE=false`.** Sin cambios respecto a F005.2.

**`DOCUMENTATION_DRIFT`.** `docs/deployment/phase_010` sigue describiendo recursos que no
existen. F005.3 no lo reescribe; queda anotado en `docs/phase-005-2/infra-audit.md`.

## Registro del primer despliegue fallido

El primer intento (`main` en `692399bb`) falló y dejó una lección que merece quedar
escrita, porque el fallo no fue el que parecía.

La comprobación de readiness usaba `filter("type:Ready")`. El operador de dos puntos
hace coincidencia laxa —gcloud avisa de ello— y devolvía `['True','True']`, así que la
comparación falló **con la revisión perfectamente lista**.

Lo grave vino después. El paso de rollback usaba `status.traffic[0].revisionName` como
«revisión actual», pero esa lista incluye las revisiones con tag, que aparecen sin
porcentaje. El elemento `[0]` era una revisión etiquetada que no servía tráfico, y el
rollback mandó el 100% a esa. Producción quedó en una revisión distinta de la que tenía
antes de empezar.

Se restauró a mano y el servicio respondió 200 en todo momento. Ambos defectos están
corregidos y cada uno tiene su guarda: el destino de rollback se filtra por `percent:100`
y aborta si no hay ninguno; la readiness usa igualdad exacta.

La moraleja no es «revisar mejor los formatos de gcloud», sino que un paso de rollback
que nunca se ejercita es un paso que no se sabe si funciona. Este se ejercitó a la
primera, y por eso apareció el defecto.
