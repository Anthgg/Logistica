# Backend de autenticación continua — Fases 9A–9C

## Objetivo

API FastAPI para autenticación tradicional y continua con PostgreSQL,
SQLAlchemy 2, Alembic, JWT de acceso, refresh rotativo y cookies HttpOnly. La
Fase 9A integra inferencia facial ArcFace, PAD MobileNetV2 y Autoencoders
conductuales por participante, normaliza sus puntajes, ejecuta fusión tardía,
aplica una política de riesgo con histéresis y persiste evaluaciones auditables.

La lógica de inferencia se incorporó en la fase 9A. La fase 9C añade una imagen
productiva separada, entrypoint, healthcheck y verificación full stack; el
entrenamiento y la evaluación académica permanecen fuera del proceso FastAPI.

## Arquitectura

Se conserva el flujo `routes -> services -> repositories -> models`. Los
runtimes de ML no acceden a SQLAlchemy; el servicio central prepara los datos,
ejecuta la inferencia pesada en el threadpool y persiste el resultado dentro de
la petición. Los modelos se inicializan una sola vez mediante el `lifespan` de
FastAPI y quedan en `app.state.model_loader`.

```text
backend/
├── app/
│   ├── api/routes/
│   │   ├── continuous_auth.py
│   │   └── model_status.py
│   ├── core/
│   │   ├── config.py
│   │   └── model_settings.py
│   ├── dependencies/continuous_auth.py
│   ├── ml/
│   │   ├── behavioral_runtime.py
│   │   ├── facial_runtime.py
│   │   ├── fusion_runtime.py
│   │   ├── model_bundle.py
│   │   ├── pad_runtime.py
│   │   └── registry.py
│   ├── models/
│   │   ├── continuous_auth_evaluation.py
│   │   └── risk_event.py
│   ├── repositories/
│   │   ├── continuous_auth_repository.py
│   │   └── risk_event_repository.py
│   ├── schemas/
│   │   ├── continuous_auth.py
│   │   ├── inference.py
│   │   └── model_status.py
│   └── services/
│       ├── behavioral_inference_service.py
│       ├── continuous_auth_service.py
│       ├── facial_inference_service.py
│       ├── fusion_service.py
│       ├── model_loader_service.py
│       ├── model_registry_service.py
│       ├── pad_inference_service.py
│       ├── risk_decision_service.py
│       └── score_normalization_service.py
├── alembic/versions/
│   └── 20260725_0006_add_continuous_authentication_inference.py
├── scripts/
│   ├── benchmark_inference.py
│   ├── calibrate_fusion.py
│   ├── calibrate_score_normalization.py
│   ├── validate_model_artifacts.py
│   └── verify_integration.py
└── tests/
```

También existe la migración equivalente de Supabase en
`supabase/migrations/20260725233000_add_continuous_authentication_inference.sql`.
Es aditiva: no elimina tablas ni sesiones existentes.

## Dependencias y versión de Python

Use Python 3.11, igual que la imagen Docker. TensorFlow CPU, NumPy, Pandas, PyArrow, Scikit-learn, Joblib,
InsightFace, ONNX Runtime, Matplotlib y psutil se declaran en
`requirements.txt`. InsightFace no descarga modelos automáticamente durante el
arranque: el directorio configurado debe contenerlos previamente.

## Variables de entorno

Las rutas son relativas al proyecto y se resuelven de forma segura:

```dotenv
MODEL_REGISTRY_PATH=../models/registry/model_registry.json
FACIAL_MODEL_VERSION=facial-arcface-v0.1.0
PAD_MODEL_VERSION=pad-mobilenetv2-v0.1.0
BEHAVIORAL_MODEL_VERSION_PREFIX=behavioral-ae
FACIAL_TEMPLATES_PATH=../models/facial/templates
FACIAL_THRESHOLD_PATH=../models/facial/thresholds
INSIGHTFACE_MODEL_ROOT=../models/facial/insightface
PAD_MODEL_PATH=../models/pad/exported
PAD_THRESHOLD_PATH=../models/pad/thresholds
BEHAVIORAL_MODELS_PATH=../models/behavioral/participants
BEHAVIORAL_FEATURES_PATH=../data/processed/behavioral/behavioral_features.parquet
NORMALIZATION_CONFIG_PATH=../models/fusion/score_normalization.json
FUSION_CONFIG_PATH=../models/fusion/fusion_config.json
MODEL_DEVICE=auto
MODEL_LOAD_ON_STARTUP=true
MODEL_STRICT_CHECKSUM=true
REQUIRE_ALL_MODELS=false
BEHAVIORAL_MODEL_LOADING_MODE=lru
BEHAVIORAL_MODEL_CACHE_SIZE=20
CONTINUOUS_AUTH_ENABLED=true
CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS=5
CONTINUOUS_AUTH_MAX_BATCH_WINDOWS=10
MINIMUM_AVAILABLE_COMPONENTS=2
INFERENCE_TIMEOUT_SECONDS=10
AUTO_REVOKE_CRITICAL_SESSION=false
RISK_HIGH_CONFIRMATION_COUNT=2
RISK_CRITICAL_CONFIRMATION_COUNT=2
RISK_RECOVERY_CONFIRMATION_COUNT=3
RISK_EVALUATION_WINDOW_SECONDS=60
```

`REQUIRE_ALL_MODELS=false` permite un arranque degradado seguro. En una
verificación estricta o antes de producción, use `true`: cualquier artefacto
obligatorio ausente o inválido detendrá el inicio.

## Registro y validación de artefactos

`ModelRegistryService` acepta únicamente modelos `candidate` o
`approved_for_integration`. Rechaza estados incompletos, checksums incorrectos,
rutas absolutas o con traversal, versiones no seleccionadas, bundles
incompletos, datasets incompatibles y cualquier registro que declare uso de
test.

Cada entrada identifica familia, tipo, versión, dataset, protocolo,
participante cuando corresponde, artefactos, SHA-256, umbral y estado. El
validador estricto abre plantillas NPZ, modelos Keras, scalers Joblib, esquemas
de características y umbrales; también verifica dimensiones compatibles. No
se registran rutas completas ni checksums completos en respuestas públicas.

```powershell
python scripts/validate_model_artifacts.py
```

## Carga en lifespan, lazy y LRU

El `ModelLoaderService` carga una sola vez:

- analizador InsightFace, plantillas y umbral facial;
- modelo PAD y su umbral;
- normalización y fusión con checksum;
- catálogo de modelos conductuales.

La estrategia conductual es configurable:

- `eager`: carga todos los participantes al arrancar;
- `lazy`: carga el participante al primer uso y lo conserva;
- `lru`: carga bajo demanda y conserva como máximo
  `BEHAVIORAL_MODEL_CACHE_SIZE`.

La caché LRU usa un lock corto para el mapa y un lock independiente por
participante. TensorFlow y el runtime facial usan locks propios; no existe un
lock global que serialice todas las modalidades.

## Inferencia y privacidad

### Facial

La imagen almacenada por el backend se decodifica, se exige exactamente un
rostro, InsightFace alinea y extrae el embedding, se aplica normalización L2 y
similitud coseno contra la plantilla del participante. El embedding de
inferencia no se persiste ni se devuelve.

### PAD

El mismo JPEG/WebP se redimensiona al tamaño del modelo y se entrega como RGB
en rango `0..255`. El modelo Keras exportado contiene el preprocesamiento de
MobileNetV2 aprendido durante entrenamiento. La salida sigmoid se interpreta
explícitamente como `attack_probability`; una probabilidad de ataque mayor
produce más riesgo.

### Conductual

El cliente solo referencia `behavioral_window_id`. El backend obtiene las
características procesadas del almacén Parquet, valida sesión, participante,
columnas, orden, NaN e infinitos, aplica `StandardScaler.transform` y calcula el
MSE del Autoencoder. Nunca ejecuta `fit`, mezcla participantes, guarda el
vector completo ni registra texto escrito.

## Normalización con validation

`ScoreNormalizationService` produce riesgo en `[0, 1]`:

- mayor similitud facial implica menor riesgo;
- mayor probabilidad de ataque PAD implica mayor riesgo;
- mayor MSE conductual implica mayor riesgo.

Admite `min_max_robust`, `logistic`, `piecewise_linear` y `empirical_cdf`. La
configuración contiene límites, umbral, dirección, estadísticas de validation,
dataset, fecha y checksum. No se incluye un JSON ficticio: debe generarse
exclusivamente desde predicciones reales de validation.

El archivo de entrada
`data/reports/integration/component_validation_predictions.parquet` requiere:
`sample_id`, `split=validation`, `dataset_version`, `component`, `score`,
`threshold`, `label` y `latency_ms`.

```powershell
python scripts/calibrate_score_normalization.py `
  --dataset-version pilot-v0.1.0
```

El script crea gráficos de distribución, el JSON de normalización y
`normalized_validation_predictions.parquet`. Rechaza rutas o metadatos de test.

## Fusión y calibración

`FusionService` implementa fusión tardía ponderada y valida que los riesgos
sean finitos y estén dentro de rango. Las estrategias disponibles son
`reject`, `renormalize_available_weights`, `use_neutral_risk` y
`require_minimum_components`. Un componente ausente nunca equivale a riesgo
cero.

```powershell
python scripts/calibrate_fusion.py `
  --dataset-version pilot-v0.1.0 `
  --weight-step 0.05 `
  --f1-tolerance 0.02
```

La búsqueda es determinista, usa solo validation, exige pesos que sumen uno y
calcula Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, FAR, FRR, EER,
matriz de confusión, disponibilidad y latencia observada. Primero conserva
candidatos dentro de la tolerancia declarada respecto del mejor F1 y después
minimiza FAR. Guarda todas las combinaciones en
`data/reports/integration/fusion_validation_search.parquet` y la seleccionada,
con límites de riesgo derivados de validation, en
`models/fusion/fusion_config.json`. Si validation no separa límites ordenados,
el script falla sin escribir una política arbitraria.

## Riesgo, niveles y máquina de estados

Los niveles de riesgo son `low`, `medium`, `high` y `critical`. Los niveles de
autenticación son `traditional`, `continuously_verified`,
`verification_required`, `restricted` y `terminated`.

- Low: mantiene la sesión y marca verificación continua.
- Medium: mantiene la sesión y aumenta observación.
- High confirmado: exige reverificación.
- Critical confirmado: restringe; solo termina si
  `AUTO_REVOKE_CRITICAL_SESSION=true`.

`RiskDecisionService` usa evaluaciones consecutivas dentro de una ventana
temporal. High y critical necesitan confirmación, y la recuperación requiere
varias mediciones confiables. Una única medición no revoca ni restringe una
sesión. La reverificación reinicia la ventana mediante
`last_continuous_verification_at`, pero conserva el historial.

## Persistencia

`continuous_auth_evaluations` guarda disponibilidad, puntajes internos,
riesgos normalizados, riesgo combinado, nivel, acción, versiones y latencia.
`risk_events` registra cambios de nivel. `sessions` incorpora
`last_risk_action` y `continuous_auth_status`; reutiliza los campos de riesgo y
autenticación ya existentes.

No se almacenan imágenes, embeddings, plantillas, contraseñas, cookies, tokens,
texto escrito ni payloads conductuales completos.

## Endpoints

- `GET /api/i18n/catalog`: catálogo público de etiquetas para el idioma
  negociado mediante `Accept-Language`.
- `GET /api/models/status`: admin o supervisor; estado sanitizado del loader.
- `POST /api/continuous-auth/evaluate`: sesión, dispositivo y CSRF válidos.
- `GET /api/continuous-auth/status`: resumen de la sesión actual.
- `GET /api/continuous-auth/evaluations`: historial paginado para admin o
  supervisor.
- `GET /api/continuous-auth/evaluations/{evaluation_id}`: detalle técnico
  autorizado sin biometría cruda.
- `POST /api/continuous-auth/reverify`: verifica la contraseña actual y
  restablece temporalmente el nivel tradicional.

`evaluate` acepta identificadores de sesión experimental, captura y ventana,
nunca scores calculados por el frontend. La respuesta normal no incluye
umbrales, MSE, pesos, rutas, embeddings ni plantillas.

## Internacionalización y contrato del frontend

El frontend envía el idioma estándar en cada solicitud:

```http
Accept-Language: en-US
```

Se admiten `es`, `en` y `pt`, incluidas variantes regionales como `es-PE`,
`en-US` y `pt-BR`. El fallback es `es`. Todas las respuestas incluyen
`Content-Language` y `Vary: Accept-Language`; CORS permite el encabezado de
entrada y expone `Content-Language`.

Los códigos de máquina, roles, estados y eventos persistidos no se traducen.
Esto mantiene estables filtros, permisos y auditoría. Los mensajes visibles y
las etiquetas aditivas sí cambian con el idioma:

```json
{
  "status": "in_transit",
  "status_label": "In transit",
  "priority": "urgent",
  "priority_label": "Urgent"
}
```

El dashboard conserva `event_type` y `resource_type`, y añade
`event_type_label` y `resource_type_label`. El timeline de envíos añade
`previous_status_label` y `new_status_label`.

`GET /api/i18n/catalog` no requiere sesión y devuelve las etiquetas de
actividad, recursos, estados, riesgo, autenticación y prioridad. Debe
consultarse al iniciar la aplicación y cada vez que cambie el idioma.

Para el listado de envíos se aceptan tanto `/api/shipments` como
`/api/shipments/`. La forma canónica es sin barra final. La respuesta es:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0,
  "total_pages": 0
}
```

Todas las llamadas autenticadas usan `credentials: "include"`. Ante un `401`,
el cliente debe ejecutar una sola vez `POST /api/auth/refresh`, también con
credenciales y CSRF, esperar su resultado y reintentar la solicitud original.
Las solicitudes concurrentes deben compartir la misma promesa de refresh para
evitar rotaciones duplicadas. Los campos `Decimal`, como `total_weight` y
`declared_value`, se serializan como cadenas para no perder precisión; el
frontend puede convertirlos solo para presentación.

## Operaciones sensibles

`require_continuous_auth_level()` permite proteger rutas seleccionadas sin
alterar masivamente la API existente. Por defecto acepta `traditional` y
`continuously_verified`, y rechaza sesiones revocadas, restringidas,
terminadas o que requieren reverificación. La dependencia debe aplicarse
gradualmente durante 9B, después de validar la experiencia de reverificación.

## Modo degradado, errores y auditoría

Si falla una modalidad, el sistema la marca no disponible y puede continuar
si se cumple la política mínima. Cada modalidad tiene timeout propio. Si no
hay componentes suficientes, la sesión queda `degraded`; no se inventa score,
no se marca low y no se cierra por una falla técnica.

Errores públicos relevantes:
`CONTINUOUS_AUTH_DISABLED`, `MODEL_REGISTRY_UNAVAILABLE`,
`MODEL_ARTIFACT_INVALID`, `FACIAL_MODEL_UNAVAILABLE`,
`PAD_MODEL_UNAVAILABLE`, `BEHAVIORAL_MODEL_UNAVAILABLE`,
`FACIAL_TEMPLATE_NOT_FOUND`, `FEATURE_SCHEMA_MISMATCH`, `INVALID_CAPTURE`,
`MULTIPLE_FACES_DETECTED`, `NO_FACE_DETECTED`, `INSUFFICIENT_COMPONENTS`,
`INFERENCE_TIMEOUT`, `FUSION_CONFIG_UNAVAILABLE`,
`REVERIFICATION_REQUIRED`, `SESSION_RESTRICTED`, `SESSION_TERMINATED` e
`INTERNAL_INFERENCE_ERROR`.

La auditoría registra carga o fallo del registro, validación o rechazo de
artefactos, evaluación, cambio de riesgo, reverificación, restricción,
terminación, timeout y fallo de componente. Los mensajes sanitizan excepciones
de ML y PostgreSQL.

## Latencia y benchmark

Cada evaluación conserva `image_decode_ms`, `facial_ms`, `pad_ms`,
`behavioral_load_ms`, `behavioral_ms`, `normalization_ms`, `fusion_ms`,
`database_ms` y `total_ms` cuando corresponden. Las tres inferencias se
despachan concurrentemente al threadpool y ninguna sesión SQLAlchemy cruza de
hilo.

```powershell
python scripts/benchmark_inference.py `
  --dataset-version pilot-v0.1.0
```

El manifiesto JSONL de benchmark debe usar `split=validation`. El informe
incluye media, mediana, desviación, P90, P95, máximo, RSS, CPU y dispositivo.
Se marca explícitamente como benchmark de integración, no evaluación final.

## Migración y verificación

```powershell
alembic heads
alembic upgrade head
python scripts/verify_integration.py
```

`verify_integration.py` comprueba registro, checksums, loader, esquema,
OpenAPI y endpoints. No escribe datos reales por defecto. La opción
`--transactional-write-test` inserta una evaluación de verificación dentro de
una transacción y ejecuta rollback explícito.

Las pruebas con PostgreSQL exigen `TEST_DATABASE_URL`. Sin esa variable se
omiten deliberadamente para no tocar la base de desarrollo o producción.

## Instalación y comandos PowerShell

```powershell
cd autenticacion-continua\backend
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env

python scripts/validate_model_artifacts.py
python scripts/calibrate_score_normalization.py `
  --dataset-version pilot-v0.1.0
python scripts/calibrate_fusion.py `
  --dataset-version pilot-v0.1.0

alembic upgrade head
python scripts/verify_integration.py
python scripts/benchmark_inference.py `
  --dataset-version pilot-v0.1.0

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -v
```

Para integración:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://usuario:clave@host:5432/base_test"
pytest -v
```

Nunca apunte `TEST_DATABASE_URL` a la base principal.

## Errores frecuentes

- `MODEL_REGISTRY_UNAVAILABLE`: falta o no es legible el registro configurado.
- `MODEL_ARTIFACT_INVALID`: revise estado, rutas relativas, SHA-256, versión,
  dataset, protocolo y `test_rows_used=0`.
- `FUSION_CONFIG_UNAVAILABLE`: ejecute las dos calibraciones con validation
  real; no cree JSON vacío.
- `INSUFFICIENT_COMPONENTS`: envíe una captura válida para facial+PAD o espere
  una ventana conductual; la ausencia no equivale a confianza.
- `FACIAL_MODEL_UNAVAILABLE`: instale InsightFace/ONNX Runtime y coloque el
  paquete local bajo `INSIGHTFACE_MODEL_ROOT`.
- `BEHAVIORAL_MODEL_UNAVAILABLE`: el participante todavía no tiene bundle
  aprobado o no coincide su versión.
- `FEATURE_SCHEMA_MISMATCH`: regenere las features con el esquema versionado;
  no reordene columnas manualmente.
- TensorFlow no instala: use Python 3.12 y reinstale el entorno virtual.
- pruebas omitidas: configure una base separada en `TEST_DATABASE_URL`.

## Preparación para Fase 9B

El frontend podrá usar cookies con `credentials: include`, obtener CSRF antes
de cada POST y consumir únicamente los seis endpoints de 9A. Debe mostrar el
estado público, solicitar contraseña en reverificación y reservar historial,
detalle y estado de modelos para admin/supervisor. No debe calcular ni enviar
scores, riesgos, pesos o features.

## Preparación para Fase 9C

Antes de desplegar la evaluación final:

1. generar artefactos y configuraciones con validation;
2. ejecutar validación estricta y benchmark;
3. probar migración y downgrade en una base separada;
4. fijar versiones y checksums;
5. construir la imagen Python 3.12;
6. usar el test congelado exactamente una vez para evaluación final.

La Fase 9A no abre, calibra ni evalúa el conjunto test.
