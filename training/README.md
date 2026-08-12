# Fases 7 y 8 — datos y entrenamiento biométrico reproducible

## Objetivo

Este módulo prepara, valida y documenta los datos del piloto de AndesLog
Operaciones S.A.C. y entrena por separado los tres candidatos de Fase 8:
ArcFace para verificación, MobileNetV2 para PAD y autoencoders conductuales
personalizados. La Fase 8 no fusiona puntajes, no usa test y no integra modelos
en FastAPI.

El pipeline usa únicamente identificadores seudonimizados. No consulta ni
exporta nombres, correos, DNI, teléfonos, direcciones, cookies, credenciales o
datos de clientes.

No es necesario esperar a crear cuentas con un rol especial: cualquier usuario
activo, incluido el administrador inicial, puede autoinscribirse mediante
`POST /api/research/participants/self-enroll`. Desde ese momento sus capturas y
eventos quedan asociados al código seudónimo devuelto. El consentimiento y las
sesiones de recolección siguen siendo obligatorios antes de que sus datos
puedan llegar a los manifiestos de entrenamiento.

## Capas de datos

- `data/raw`: fuente inmutable. El pipeline calcula su huella SHA-256 antes y
  después de cada ejecución y falla si cambia.
- `data/interim`: índices de calidad, lotes numéricos ya validados y ventanas
  temporales. Las capturas originales no se copian ni reemplazan.
- `data/processed`: métricas faciales y características conductuales sin
  eventos crudos.
- `data/manifests`: fuente técnica Parquet, particiones, versión y test
  congelado.
- `data/reports/pilot`: auditoría, tablas, gráficos, informe y readiness.

Las carpetas de salida se crean al ejecutar el pipeline. `data/raw/facial` es la
ruta de lectura configurada y debe ser aprovisionada por el flujo de captura
existente, no por estos scripts.

La ingestión autorizada se realiza con `export_facial_raw.py`: descarga desde
el bucket privado configurado, compara el SHA-256 de PostgreSQL y crea archivos
nuevos. Nunca reemplaza un archivo raw existente; si encuentra una diferencia,
detiene la exportación.

## Protocolo piloto

El protocolo inicial requiere cinco participantes reales, consentimiento
vigente y un mínimo configurable de cuatro sesiones por participante:

1. Enrolamiento facial, 3–5 minutos.
2. Operación logística legítima, 10–15 minutos.
3. Cambio controlado de operador, 5–10 minutos.
4. PAD controlado: genuino, foto impresa, foto en pantalla y video reproducido.

La columna `scenario` conserva uno de los escenarios logísticos admitidos por
el backend. El propósito biométrico de cada sesión se confirma en PostgreSQL
mediante `PATCH /api/research/sessions/{session_id}/annotation`. La API guarda
rol de muestra, identidad, cambio de operador, etiqueta PAD, tipo y dispositivo
de ataque, versión del protocolo y trazabilidad de la anotación. Las sesiones
con `annotation_status != confirmed` se rechazan durante la preparación.

`configs/pilot_protocol.yaml` mantiene `session_annotations` únicamente como
respaldo controlado para fixtures y datos históricos; no convierte una sesión
sin confirmación en una sesión válida. Ejemplo de la representación equivalente:

```yaml
session_annotations:
  00000000-0000-0000-0000-000000000001:
    identity_label: genuine
    sample_role: enrollment
  00000000-0000-0000-0000-000000000002:
    identity_label: genuine
    sample_role: change_operator
    operator_change_at: "2026-07-24T15:30:00-05:00"
  00000000-0000-0000-0000-000000000003:
    presentation_label: attack
    attack_type: printed_photo
    source_device: controlled-printer-01
    pad_source_id: controlled-print-01
```

No se infiere una etiqueta PAD ni un cambio de operador. La persona que actúe
como impostor también debe ser participante consentido. No se deben usar
imágenes de redes sociales.

## Requisitos e instalación

Se requiere Python 3.11 para compatibilidad con TensorFlow, InsightFace y
ONNX Runtime. En Windows PowerShell:

```powershell
cd autenticacion-continua\training
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Las dependencias están limitadas a procesamiento tabular, imágenes, validación,
PostgreSQL, estadística, gráficos y pruebas. No se incluyen PyTorch,
TensorFlow, InsightFace ni ONNX Runtime. OpenCV Haar se usa exclusivamente para
contar rostros y estimar su caja; nunca identifica personas.

## Variables de entorno

Copiar `.env.example` a `.env` y definir:

```dotenv
DATABASE_URL=postgresql://usuario:contrasena@host:5432/base
```

También se reconoce `../backend/.env`. Nunca confirmar `.env` al repositorio ni
mostrar la URL completa en logs.

## Configuración YAML

- `pilot_protocol.yaml`: protocolo, escenarios, mínimos, consentimiento,
  anotaciones controladas y semilla.
- `data_pipeline.yaml`: rutas, versión, 60/20/20 y controles de fuga.
- `face_quality.yaml`: formatos, tamaño, brillo, contraste, enfoque, rostro,
  intervalo y tasa máxima de rechazo.
- `behavioral_features.yaml`: ventana de 30 s, desplazamiento de 10 s, actividad,
  límites temporales y tolerancia de valores faltantes.

Los valores metodológicos no se duplican en scripts.

## Auditoría y calidad facial

`audit_raw_data.py` contrasta sesiones, contadores, consentimiento, archivos
faltantes y duplicados. Produce:

- `raw_data_audit.parquet`
- `raw_data_audit.csv`

El analizador facial verifica existencia, lectura, formato, bytes, dimensiones,
checksum, duplicación, brillo, contraste, desenfoque, cantidad y tamaño de
rostros, proximidad al borde, visibilidad e intervalo temporal. Una captura
puede conservar varios motivos de rechazo; jamás se elimina.

## Validación conductual

Los lotes JSONB se validan por identificador, secuencias, orden, límites de
sesión, tipos, categorías, rangos y valores finitos. La detección de propiedades
prohibidas es recursiva. Si aparecen `key`, `code`, `text`, `password` u otra
propiedad textual bloqueada, el lote queda inválido con
`FORBIDDEN_TEXTUAL_DATA_DETECTED`, sus eventos no continúan y su contenido no se
imprime ni se copia al reporte.

## Ventanas y características

Las ventanas iniciales duran 30 segundos y avanzan 10 segundos. Nunca mezclan
sesiones ni cruzan un `operator_change_at`. Todas las ventanas superpuestas de
un segmento comparten `segment_id`.

Las características de teclado describen dwell, flight, intervalos, tasas,
correcciones, modificadores, navegación, pausas y ráfagas. Las de mouse
describen movimientos, clics, scroll, distancia, velocidad, aceleración,
dirección, inactividad, rectitud y coordenadas normalizadas agregadas. No se
guardan teclas, palabras, selectores, identificadores HTML ni eventos crudos en
`behavioral_features.parquet`.

No se ajusta `StandardScaler`. Se genera estadística descriptiva de valores
faltantes, infinito y varianza cero para que un escalador futuro se ajuste solo
con entrenamiento.

## Manifiestos y particiones

Los tres manifiestos incluyen versión, protocolo, fecha, sesión fuente,
participante, checksum, calidad, rechazos y split. Las rutas de archivos son
relativas.

- Identidad: división por sesión dentro de participante.
- Conducta: división por segmento; las ventanas superpuestas permanecen juntas.
- PAD: prioriza participantes distintos y agrupa sesión, dispositivo y fuente
  del ataque. Con cinco participantes es solo exploratoria.

La asignación 60/20/20 es determinista mediante `random_seed`. El
`leakage_checker` detiene el pipeline ante UUID, checksum, sesión, evento,
ventana, segmento, solapamiento temporal u origen PAD compartido entre splits.

## Congelamiento y versionado

`freeze_test_set.py` selecciona solo `test`, ordena de forma estable y genera:

- `frozen_test_manifest.parquet`
- `frozen_test_manifest.sha256`
- `frozen_test_metadata.json`

Una ejecución normal no reemplaza estos archivos. Para una corrección
excepcional:

```powershell
python scripts/freeze_test_set.py --force `
  --force-reason "Motivo metodológico documentado"
```

El archivo `dataset_metadata.json` registra versión `pilot-v0.1.0`, protocolo,
hash de configuración, commit Git disponible y cantidades. El piloto nunca se
denomina `final` o `definitive`.

El test congelado no se utiliza para umbrales, arquitectura, pesos,
hiperparámetros, selección de características ni reglas de descarte.

## Informe y readiness

`pilot_report.md` resume protocolo, participantes, sesiones, escenarios,
duraciones, capturas, lotes, eventos, ventanas, rechazos, particiones, fugas,
incidentes, limitaciones y recomendaciones. Se generan CSV y gráficos
individuales con Matplotlib.

`readiness_assessment.json` devuelve `ready`, `ready_with_observations` o
`not_ready`. Es `not_ready` si faltan cinco participantes consentidos, sesiones
del protocolo, datos válidos, particiones completas, test congelado, si existen
incidentes graves, texto prohibido, duplicación crítica o fugas.

La ausencia actual de evidencia real nunca se reemplaza por registros
inventados: primero se ejecuta el piloto autorizado y luego se repite el
pipeline.

## Comandos

```powershell
python scripts/audit_raw_data.py
python scripts/export_facial_raw.py --dry-run
python scripts/export_facial_raw.py
python scripts/analyze_face_quality.py
python scripts/validate_behavioral_events.py
python scripts/build_behavioral_windows.py
python scripts/extract_behavioral_features.py
python scripts/build_manifests.py
python scripts/split_datasets.py
python scripts/freeze_test_set.py
python scripts/generate_pilot_report.py

python scripts/run_preparation_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --freeze-test

pytest -v
```

Filtros disponibles: `--participant-id`, `--session-id`, `--config` y
`--dry-run`. El modo `dry-run` consulta y valida, pero no escribe salidas. El
pipeline completo solo congela test si se pasa `--freeze-test` y existen filas
test.

## Pruebas

Las 40 pruebas cubren inmutabilidad de raw, calidad facial, texto prohibido,
eventos, ventanas, cambio de operador, características, manifiestos,
particiones, fugas, congelamiento, informe, readiness y pipeline completo.

```powershell
pytest -v
```

## Privacidad

- Usar únicamente UUID seudonimizados.
- Mantener las capturas en almacenamiento autorizado.
- No copiar datos de autenticación ni entidades logísticas.
- No imprimir payloads.
- Retirar al participante y excluir sus datos conforme al proceso de
  consentimiento del backend.
- Revisar manualmente las anotaciones controladas antes de congelar test.

## Errores frecuentes

- `DATABASE_URL` ausente: crear `.env` o comprobar `../backend/.env`.
- `FILE_NOT_FOUND`: verificar que `storage_path` sea relativo a
  `capture_storage_root`.
- `FORBIDDEN_TEXTUAL_DATA_DETECTED`: corregir el colector; no rescatar ni copiar
  el contenido del lote.
- `CriticalLeakageError`: revisar la unidad de agrupación; no desactivar el
  control.
- Sin split validation/test: se necesitan más sesiones o segmentos por
  participante.
- Test ya congelado: no usar `--force` salvo una corrección justificada.
- `not_ready`: consultar `critical_failures` y corregir la recolección; no
  reinterpretarlo como aprobación.

## Fase 8: arquitectura y protección de test

- ArcFace usa el paquete preentrenado `buffalo_l` de InsightFace. No se entrena
  ArcFace desde cero. Se extraen embeddings L2, se construyen plantillas con
  media normalizada y se calibra similitud coseno con validation.
- PAD usa MobileNetV2 preentrenada, primero con backbone congelado y después
  con fine-tuning de los últimos bloques. La salida representa probabilidad de
  ataque; el umbral se calibra por ACER o APCER objetivo, no se fija en 0.5.
- Conducta usa un `StandardScaler` y autoencoder por participante. Ambos se
  ajustan únicamente con ventanas legítimas train. Validation genuina e
  impostora se reserva para umbrales y métricas.

`verify_training_inputs.py` comprueba columnas, archivos, SHA-256, versiones,
calidad, particiones, sesiones y checksums compartidos, ventanas solapadas,
texto prohibido, NaN, infinito y la integridad del test congelado. Los loaders
solo devuelven train y validation. Los metadatos exportados registran
`test_rows_used: 0`.

El test congelado no se utiliza para seleccionar arquitectura, hiperparámetros,
plantillas, scalers, pesos o umbrales. Se reservará para la evaluación final.

## Configuraciones de entrenamiento

- `configs/arcface.yaml`: modelo, proveedores ONNX, detección, enrolamiento y
  objetivos FAR/EER.
- `configs/pad_mobilenetv2.yaml`: imagen, fases, tasas de aprendizaje,
  aumentación, callbacks y objetivo ACER.
- `configs/behavioral_autoencoder.yaml`: orden explícito de características,
  mínimos, arquitectura, regularización y umbral.
- `configs/experiment.yaml`: versión, rutas, registro y protección de test.

No hay hiperparámetros científicos ocultos en el código. Las semillas se
aplican a `random`, NumPy y TensorFlow cuando está instalado. Algunas
operaciones GPU pueden seguir sin ser absolutamente deterministas; esa
limitación se registra.

## Métricas

- Facial: FAR, FRR, EER, ROC-AUC, precision, recall, F1 y matriz de confusión.
- PAD: APCER, BPCER, ACER, ROC-AUC, PR-AUC y desgloses por ataque,
  participante, sesión y dispositivo cuando existe.
- Conductual: FAR, FRR, EER, ROC-AUC, PR-AUC, F1 y distribuciones MSE por
  participante, además de resumen macro.

APCER es la proporción de ataques aceptados como bona fide. BPCER es la
proporción bona fide rechazada como ataque. ACER es su promedio. En conducta y
facial, FAR representa impostores aceptados y FRR usuarios genuinos rechazados.

## Artefactos y versionado

Los artefactos se guardan bajo `models/facial`, `models/pad`,
`models/behavioral` y `models/registry`. Los modelos pesados están ignorados
por Git. Cada candidato contiene versión explícita, configuración, dataset,
protocolo, métricas y SHA-256. No se usan nombres como `final` o `final2`.

`experiments.parquet` registra ejecuciones `running/completed/failed/cancelled`;
el código nunca marca `completed` si falta un artefacto.
`model_registry.json` usa los estados `experimental`, `candidate`, `rejected`
y `approved_for_integration`. Fase 8 solo genera `candidate` o `rejected`.

## Comandos de Fase 8

```powershell
cd autenticacion-continua\training

python scripts/verify_training_inputs.py `
  --dataset-version pilot-v0.1.0

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models facial `
  --device auto

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models pad `
  --device cpu

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models behavioral `
  --participant-id P-0001 `
  --experiment-name ae-p0001-baseline `
  --device cpu

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models all `
  --device auto

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models all `
  --device cpu `
  --dry-run

python scripts/run_training_pipeline.py `
  --dataset-version pilot-v0.1.0 `
  --models pad `
  --device auto `
  --resume

python scripts/generate_training_report.py `
  --dataset-version pilot-v0.1.0

pytest -v
```

`--device auto` selecciona GPU solo cuando TensorFlow y ONNX Runtime exponen
proveedores compatibles; de lo contrario usa CPU con un mensaje claro.
No se deben instalar simultáneamente `onnxruntime` y `onnxruntime-gpu`.

## Reanudación y errores frecuentes de Fase 8

- PAD reanuda desde `best_finetuned.keras`.
- Conducta omite modelos completados y puede reanudar participantes pendientes.
- Un participante conductual sin muestras suficientes queda registrado como
  no entrenable; no se inventan ventanas.
- Un fallo PAD detiene el pipeline PAD y conserva checkpoints.
- Una captura ArcFace rechazada queda en `facial_rejections.csv`; el pipeline
  continúa solo si todavía hay enrolamiento suficiente.
- `TensorFlow no está instalado`: recrear el entorno con Python 3.11.
- `Faltan artefactos del test congelado`: completar Fase 7 y congelar test, no
  crear archivos vacíos manualmente.
- Manifiestos con cero filas: ejecutar el piloto, exportar capturas y repetir
  el pipeline de preparación.

## Preparación para la Fase 9

La Fase 9 podrá comenzar cuando existan candidatos trazables para las tres
familias. Allí se implementarán la fusión, el puntaje de riesgo, la inferencia
FastAPI y la evaluación única con test. Nada de eso se ejecuta en Fase 8.
