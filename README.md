# Autenticación continua multimodal

Backend FastAPI y entorno reproducible para la tesis sobre autenticación continua
mediante biometría facial, PAD, comportamiento de teclado/mouse y fusión tardía.
La aplicación logística ficticia es AndesLog Operaciones S.A.C.

La infraestructura de la fase 9C está preparada para iniciar PostgreSQL, API y
servidor web con Docker Compose. La evaluación científica vive en una imagen
separada y solo puede abrir el test congelado después de superar controles
explícitos de integridad y aprobación.

## Estado verificable

- La API, las migraciones y las pruebas backend ya existen.
- Las imágenes usan Python 3.11 o Node 22 y usuarios no root.
- `models`, `data/manifests` y `data/processed` se montan como solo lectura.
- PostgreSQL usa el volumen persistente `postgres_data`.
- `evaluation` no inicia con el stack: requiere el profile `evaluation`.
- El directorio `frontend` es el contenedor web mínimo de integración. El
  frontend React empresarial se mantiene fuera de este repositorio y puede
  sustituir su etapa de build conservando el contrato de Nginx.
- En esta copia no existen todavía los pesos, registro completo, aprobación
  técnica ni manifiesto test congelado. Por esa razón la evaluación final debe
  permanecer bloqueada; no se inventan artefactos, aprobaciones ni métricas.

## Arquitectura

```text
Navegador :8080
    │
    ├── Nginx no privilegiado (SPA y cabeceras)
    └── FastAPI :8000
            ├── PostgreSQL :5432 (red interna y volumen)
            ├── models/ (solo lectura)
            ├── data/processed/ (solo lectura)
            └── data/captures/ (escritura persistente)

evaluation (profile explícito)
    ├── models/ (solo lectura)
    ├── data/manifests/ (solo lectura)
    ├── data/processed/ (solo lectura)
    └── data/reports/final/ (escritura)
```

Un solo worker de Uvicorn evita duplicar los modelos en RAM. Aumente
`WEB_CONCURRENCY` únicamente después de medir memoria, latencia y concurrencia.

## Estructura relevante

```text
backend/                 FastAPI, Alembic, Dockerfile y entrypoint
frontend/                build web, Nginx y comprobación de humo
training/                pipeline previo e imagen exclusiva de evaluación
evaluation/              gates, evaluadores, estadística, informes y tests
infrastructure/          contratos operativos y verificación de contenedores
models/                  artefactos externos; nunca se escriben desde servicios
data/captures/           capturas persistentes autorizadas
data/manifests/          manifiestos, incluido test congelado, solo lectura
data/processed/          datos procesados, solo lectura
data/reports/final/      lock, marcadores, resultados e informe final
compose.yaml             desarrollo local
compose.production.yaml  endurecimiento para producción
```

## Requisitos

- Docker Desktop con Docker Compose v2.
- Al menos 10 GB libres para la imagen de evaluación y sus capas.
- Artefactos aprobados en `models/` para inferencia real.
- Manifiestos y archivos procesados con los hashes aprobados.

Copie `.env.example` a `.env` y cambie todos los marcadores. No versionar `.env`.
Genere `SECRET_KEY` y `POSTGRES_PASSWORD` aleatorios y distintos.

## Variables principales

| Variable | Uso |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Base local persistente |
| `SECRET_KEY` | Firma de sesión/JWT; secreto del backend |
| `FRONTEND_URL` | Origen CORS exacto |
| `COOKIE_SECURE` | `false` en HTTP local, `true` en HTTPS |
| `SESSION_COOKIE_SAMESITE` | `lax` local, `none` entre dominios HTTPS |
| `VITE_API_URL` | URL pública visible desde el navegador |
| `VITE_COMPANY_NAME`, `VITE_APP_NAME`, `VITE_APP_ENV` | Metadatos públicos |
| `MODEL_LOAD_ON_STARTUP` | Carga controlada de modelos |
| `REQUIRE_ALL_MODELS` | Falla si falta un componente |
| `VALIDATE_MODELS_ON_STARTUP` | Comprueba registry y checksums |
| `WEB_CONCURRENCY` | Workers de Uvicorn; valor inicial `1` |

Nunca coloque secretos en variables `VITE_*`: se incorporan al JavaScript
entregado al navegador.

## Inicio local

```powershell
docker compose build
docker compose up -d postgres
docker compose up -d backend
docker compose up -d frontend
docker compose ps
```

El equivalente en un comando es:

```powershell
docker compose up -d --build
```

Comprobaciones:

```powershell
curl.exe http://localhost:8000/api/health
curl.exe http://localhost:8080/
docker compose logs -f backend
docker compose logs -f frontend
```

Para detener sin borrar PostgreSQL:

```powershell
docker compose down
docker compose down --remove-orphans
```

No ejecute `docker compose down -v` salvo que pretenda eliminar el volumen y
todos los datos locales de PostgreSQL.

## Migraciones y modelos

El entrypoint espera PostgreSQL, ejecuta `alembic upgrade head`, valida modelos
si se habilita la opción y finalmente inicia Uvicorn. No entrena ni calibra.

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/validate_model_artifacts.py
```

En desarrollo se permite `REQUIRE_ALL_MODELS=false` para que los módulos no
disponibles aparezcan degradados. Producción usa validación estricta y debe
arrancar únicamente con el registry, versiones y checksums auténticos.

## Cookies, CORS y CSRF

Desarrollo local:

```dotenv
FRONTEND_URL=http://localhost:8080
VITE_API_URL=http://localhost:8000/api
COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
```

Producción con dominios HTTPS distintos:

```dotenv
FRONTEND_URL=https://frontend.example
VITE_API_URL=https://backend.example/api
COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
```

CORS debe contener el origen exacto y `allow_credentials=true`; no puede usar
`*`. El frontend debe enviar `credentials: "include"` y el encabezado CSRF en
operaciones mutables. La CSP de Nginx permite `localhost:8000` y hosts HTTPS de
Cloud Run, sin `unsafe-eval`; la cámara se limita al propio origen y el micrófono
está deshabilitado.

## Verificación full stack

Con el stack saludable:

```powershell
docker compose exec backend python scripts/verify_full_stack.py `
  --api-url http://backend:8000/api `
  --frontend-url http://frontend:8080 `
  --frontend-origin http://localhost:8080
```

El verificador crea únicamente registros con prefijo `integration-test-`,
comprueba migración, health, OpenAPI, registro, cookies, login, refresh, CSRF,
rutas logísticas, investigación, riesgo, modelos, logout y auditoría, y después
elimina solo sus propios datos. No utiliza participantes reales ni el test
congelado.

La persistencia se verifica reiniciando el backend, no PostgreSQL:

```powershell
python infrastructure/scripts/verify_restart_persistence.py
```

Este verificador inserta un probe `integration-test-persistence-*`, reinicia el
backend, confirma el registro desde una conexión nueva, revisa nuevamente la
salud y la validación de modelos, y elimina el probe. Si no hay artefactos
aprobados, la persistencia puede aprobar mientras la recarga de modelos queda
marcada honestamente como bloqueada.

## Seguridad de las imágenes

Después de construir las tres imágenes:

```powershell
python infrastructure/scripts/verify_container_security.py
```

La comprobación valida usuario no root, ausencia de `.env`, Git, tests
productivos, `data/raw`, test y modelos dentro de las imágenes; también valida
healthchecks, profile de evaluación y montajes de solo lectura.

`compose.production.yaml`:

- no publica PostgreSQL;
- exige `POSTGRES_PASSWORD`, `SECRET_KEY` y `FRONTEND_URL`;
- activa cookies seguras, modelos obligatorios y validación de artefactos.

Validación sin desplegar:

```powershell
$env:POSTGRES_PASSWORD="valor-temporal"
$env:SECRET_KEY="valor-temporal-de-al-menos-32-caracteres"
$env:FRONTEND_URL="https://frontend.example"
docker compose -f compose.yaml -f compose.production.yaml config --quiet
```

## Protocolo del test congelado

Antes de la ejecución final deben existir y coincidir:

- `data/manifests/frozen_test_manifest.parquet`
- `data/manifests/frozen_test_manifest.sha256`
- `data/manifests/frozen_test_metadata.json`
- `models/registry/model_registry.json`
- `models/registry/integration_approval.json` con estado
  `approved_for_final_evaluation`
- pesos, plantillas, scalers, umbrales, normalización, fusión y variantes de
  ablación referenciados por la aprobación

La verificación controla versión de dataset/protocolo, hashes de manifiesto y
muestras, duplicados con train/validation, sesiones, ventanas, columnas
textuales, fechas y checksums de modelos. Si falla, se detiene antes de inferir.

El archivo `models/registry/integration_approval.json` incluido actualmente es
un bloqueo honesto y no una aprobación. Debe ser reemplazado por el responsable
técnico solo después de integrar y congelar artefactos reales.

## Dry-run seguro

Construya la imagen y ejecute:

```powershell
docker compose --profile evaluation run --rm --no-deps evaluation `
  python evaluation/scripts/run_final_evaluation.py `
  --config evaluation/configs/final_evaluation.yaml `
  --dry-run
```

El dry-run revisa configuración, rutas, aprobación y sidecars sin abrir el
contenido del test para inferencia. No crea `evaluation_lock.json`, marcadores
de inicio/finalización, predicciones ni métricas.

## Ejecución final única

Solo después de un dry-run aprobado y una revisión humana:

```powershell
docker compose --profile evaluation run --rm evaluation `
  python evaluation/scripts/run_final_evaluation.py `
  --config evaluation/configs/final_evaluation.yaml `
  --device auto
```

El orquestador crea el lock y el marcador de inicio antes de abrir el test.
Conserva modelos, umbrales, pesos, semilla, versiones y hashes. Una segunda
ejecución accidental se bloquea. Una repetición técnica requiere simultáneamente
`--authorized-rerun` y `--rerun-reason`; el incidente queda registrado y no
autoriza cambiar decisiones científicas.

No elimine manualmente:

- `data/reports/final/evaluation_lock.json`
- `data/reports/final/test_evaluation_started.json`
- `data/reports/final/test_evaluation_completed.json`
- registros de error o ejecución

## Evaluación y estadística

El pipeline ejecuta, sobre una única carga controlada de predicciones:

1. facial: ROC/PR, FAR, FRR, EER, TAR, rechazos y desgloses;
2. PAD: APCER, BPCER, ACER, ataques, dispositivos y participantes;
3. comportamiento: resultados agregados y por participante;
4. fusión: disponibilidad, histéresis, falsas alertas y tiempo de detección;
5. ablaciones aprobadas con la misma población y sin renormalización posterior;
6. comparación pareada pretest/postest por sesión experimental;
7. latencia cold/warm, memoria y tamaño de modelos;
8. McNemar, t pareada o Wilcoxon, Friedman, Holm, intervalos y efectos;
9. CSV para SPSS, tablas, figuras independientes, XLSX, informe y checksums.

La concurrencia 1/5/10 requiere una fixture local de validación separada para no
repetir el test científico. Nunca se ejecuta carga contra producción sin
autorización. No se presentan métricas si no fueron calculadas.

## Pruebas

Frontend:

```powershell
Set-Location frontend
npm run test:run
npm run typecheck
npm run build
Set-Location ..
```

Backend:

```powershell
docker compose exec backend pytest -v
```

Evaluación, exclusivamente con fixtures sintéticas y directorios temporales:

```powershell
docker compose --profile evaluation run --rm --no-deps evaluation `
  python -m pytest evaluation/tests -v
```

Estas pruebas no abren el test real, no crean el lock definitivo y no recalibran
ningún modelo.

## Informes, privacidad y reproducibilidad

Una ejecución final válida escribe bajo `data/reports/final`:

- predicciones y métricas por componente;
- ablación, comparación, rendimiento y estadística;
- figuras Matplotlib sin imágenes faciales;
- `final_evaluation_report.md`, JSON, XLSX y CSV para tesis;
- `run_metadata.json`, `reproduce.md` y checksums.

El generador seudonimiza como `P-0001`, elimina identificadores directos y
rechaza informes con correos, teléfonos, direcciones, texto capturado, cookies,
tokens, contraseñas, embeddings o rutas internas. La tabla de vinculación no se
publica.

## Cloud Run

La imagen backend respeta `PORT`, proxy headers y logs por stdout. Para desplegar:

- use Cloud SQL o Supabase y Secret Manager;
- configure memoria, CPU, timeout y concurrencia a partir de mediciones;
- use almacenamiento de objetos para capturas duraderas;
- no dependa del sistema de archivos efímero;
- configure `FRONTEND_URL`, cookies HTTPS y CORS exactos;
- entregue modelos por imagen versionada o descarga verificada en el arranque.

La API conocida durante esta fase fue:

`https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api`

No está codificada como única URL válida: el build del frontend acepta
`VITE_API_URL` y la CSP admite hosts de Cloud Run.

## Solución de problemas

- Backend no saludable: revise `docker compose logs backend`, conexión y
  migraciones.
- Modelos degradados: ejecute `validate_model_artifacts.py` y compare registry,
  rutas y hashes.
- Cookie ausente: confirme HTTPS, `SameSite`, `Secure`, CORS y
  `credentials: "include"`.
- CSRF 403: obtenga la cookie/token actual y envíe el encabezado previsto.
- Frontend no llama a la API: `VITE_API_URL` debe ser accesible desde el
  navegador, no `http://backend:8000`.
- Dry-run bloqueado: no lo fuerce; resuelva únicamente los artefactos reales que
  el informe identifica.
- Evaluación iniciada e incompleta: conserve lock, marcador y logs; documente el
  fallo técnico antes de solicitar una repetición autorizada.

Consulte también `backend/README.md`, `evaluation/README.md` e
`infrastructure/README.md`.
