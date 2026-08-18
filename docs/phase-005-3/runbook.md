# Runbook — despliegue productivo y rotación de secretos

Ningún paso pide, muestra ni transporta un valor secreto en claro.

## Desplegar

### PRECHECK

| Comprobación | Criterio |
|---|---|
| `main` verde en CI | El SHA a desplegar tiene ejecución `success` |
| Revisión Alembic productiva | `jl480110048dk` — el código a desplegar debe ser compatible |
| Revisión actual de Cloud Run | Anotada como destino de rollback |
| Secretos en Secret Manager | `DATABASE_URL_PRODUCTION` y `SECRET_KEY_PRODUCTION` con versión habilitada |

### EXECUTE

GitHub → Actions → *Production Deployment Pipeline* → Run workflow.

- `commit_sha`: vacío usa el SHA de la ejecución; para desplegar un `main` concreto,
  indícalo.
- `promote_traffic`: `true` promueve tras verificar; `false` deja la revisión creada sin
  tráfico para inspeccionarla por su URL con tag.

### VERIFY

El workflow ya comprueba `Ready`, el health y que `/api/logistics/catalogs/countries`
no devuelva 404. Verificación manual adicional:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://<servicio>/health
```

Y la trazabilidad completa, que es lo que convierte «parece la versión nueva» en un
hecho:

```bash
gcloud run services describe <servicio> --region=<región> \
  --format='value(status.traffic[0].revisionName)'
gcloud run revisions describe <revisión> --region=<región> \
  --format='value(status.imageDigest)'
```

El digest debe coincidir con el que publicó la ejecución del workflow, y su etiqueta con
el SHA de `main`.

### FAILURE

| Síntoma | Acción |
|---|---|
| La revisión no queda `Ready` | Ver logs de la revisión. El tráfico no se movió; no hay impacto |
| Health distinto de 200 | El workflow revierte solo. Investigar antes de reintentar |
| Catálogos con 404 tras desplegar | La imagen no lleva el código nuevo: revisar el SHA construido |
| 5xx tras promover | Revertir tráfico a la revisión anterior de inmediato |

Rollback manual:

```bash
gcloud run services update-traffic <servicio> --region=<región> \
  --to-revisions=<revisión-anterior>=100
```

## Rotar `SECRET_KEY`

Se puede hacer sin intervención humana y sin que el valor toque una terminal: se genera
y se envía por tubería a Secret Manager en un solo paso, y el servicio lo consume por
referencia.

1. Añadir una versión nueva al secreto `SECRET_KEY_PRODUCTION` generando el valor con
   `secrets.token_urlsafe(48)` **redirigido directamente** a `gcloud secrets versions
   add --data-file=-`. Nunca a fichero, nunca a pantalla.
2. Desplegar una revisión nueva. Cloud Run lee la versión `latest` al arrancar; una
   revisión ya en marcha conserva la que leyó.
3. Comprobar que un login nuevo funciona.

**Efecto esperado y aceptado**: los JWT emitidos con la clave anterior dejan de validar.
Los usuarios tendrán que iniciar sesión otra vez. CSRF no se ve afectado.

## Rotar la contraseña de la base

El primer paso **no se puede automatizar**: en Supabase el rol `postgres` no tiene
permiso para cambiar su propia contraseña por SQL. Un intento de
`ALTER USER postgres WITH PASSWORD ...` falla con `InsufficientPrivilege`, así que la
rotación sale del panel o de la API de gestión.

### 1. Rotar en Supabase

Project Settings → Database → *Reset database password*. Copiar el valor nuevo al
portapapeles. No pegarlo en un chat, un ticket ni un fichero.

A partir de ese momento la base solo acepta la contraseña nueva, y el secreto todavía
guarda la anterior: **el servicio se degrada en cuanto arranque una instancia nueva**.
Conviene encadenar los pasos siguientes sin pausas.

### 2. Publicar la versión nueva del secreto

```bash
python backend/scripts/rotate_database_url.py
```

Pide la contraseña por entrada oculta, reutiliza usuario, host, puerto y base de la
versión vigente, comprueba que la credencial conecta **antes** de publicar nada, y
después verifica que la anterior ya no autentica. El valor no pasa por la línea de
comandos, ni por el historial, ni por un fichero temporal, ni por la pantalla.

Si prefieres no usar la terminal: Consola de GCP → Secret Manager →
`DATABASE_URL_PRODUCTION` → *Nueva versión*, y pegar la cadena completa en el editor.

### 3. Desplegar una revisión nueva

Una revisión en marcha conserva el valor que leyó al arrancar; solo una revisión nueva
lee la versión nueva del secreto.

### 4. Verificar

- `/health` responde 200.
- El Job de migraciones en modo `verify-only` conecta y reporta `jl480110048dk`.
- Deshabilitar la versión anterior del secreto.
- Comprobar que la credencial anterior ya no autentica.

## Qué no hacer

- Pasar un secreto por `--set-env-vars`: acaba en logs e historial.
- Escribir un secreto en `$GITHUB_OUTPUT` o `$GITHUB_ENV`.
- Usar `set -x` cerca de un comando con secretos.
- Conservar la clave anterior «para no cerrar sesiones».
- Crear organizaciones, sedes o almacenes de prueba en producción para verificar el
  despliegue. Los endpoints de lectura bastan.
