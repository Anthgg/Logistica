# Fase 7.5 — datasets biométricos externos

## Resultado actual

La infraestructura de incorporación está implementada, pero los datasets no se
consideran descargados ni los experimentos completados. El estado de preparación
es `not_ready` hasta que existan licencias, archivos, checksums, manifiestos con
muestras y resultados verificables.

No se consumió el test propio congelado y no se fabricaron métricas.

## Registro y licencias

La fuente de verdad es `external-data/registry/datasets.yaml`. Una descarga solo
puede empezar si el registro está en `approved`, tiene una copia local de licencia,
evidencia del acuerdo cuando corresponda, URL directa oficial, host permitido y
SHA-256 esperado.

Revisión realizada el 26 de julio de 2026:

| Dataset | Estado | Motivo principal |
|---|---|---|
| OULU-NPU | `agreement_required` | EULA y aprobación institucional |
| Replay-Attack | `agreement_required` | EULA; investigación no comercial |
| Replay-Mobile | `agreement_required` | EULA; investigación no comercial |
| CelebA-Spoof | `agreement_required` | investigación no comercial; no redistribución |
| SiW | `agreement_required` | Dataset Release Agreement de MSU |
| SiW-Mv2 | `agreement_required` | DRA de MSU y credenciales temporales |
| CASIA-SURF CeFA | `agreement_required` | registro y acuerdo |
| CMU Keystroke | `pending_review` | no se identificó una licencia explícita |
| Aalto 136M | `pending_review` | uso científico/no comercial; revisar `readme.txt` |
| Balabit Mouse | `pending_review` | repositorio sin licencia explícita |
| Behaviour Biometrics | `pending_review` | CC BY 4.0; falta copia local y enlace directo verificado |

`pending_review` no significa rechazo: evita asumir permisos no documentados.

## Comandos

Ejecutar desde la raíz del repositorio con el entorno de `training`:

```powershell
.\training\.venv\Scripts\python.exe scripts\register_external_datasets.py
.\training\.venv\Scripts\python.exe scripts\verify_dataset_licenses.py
.\training\.venv\Scripts\python.exe scripts\validate_external_dataset.py replay_attack
```

Los cinco descargadores solicitados aceptan `--expected-sha256`. Mientras el
dataset no esté aprobado, solo generan instrucciones:

```powershell
.\training\.venv\Scripts\python.exe scripts\download_replay_attack.py
.\training\.venv\Scripts\python.exe scripts\download_celeba_spoof.py
.\training\.venv\Scripts\python.exe scripts\download_cmu_keystroke.py
.\training\.venv\Scripts\python.exe scripts\download_balabit_mouse.py
.\training\.venv\Scripts\python.exe scripts\download_behaviour_biometrics.py
```

Después de registrar una descarga autorizada:

```powershell
.\training\.venv\Scripts\python.exe scripts\extract_pad_frames.py replay_attack --frames-per-second 2
.\training\.venv\Scripts\python.exe scripts\adapt_external_keystrokes.py cmu_keystroke --input RUTA --cmu-wide
.\training\.venv\Scripts\python.exe scripts\adapt_external_mouse.py balabit_mouse --input RUTA
```

Los adaptadores solo aceptan entradas ubicadas dentro del directorio `raw` del
dataset y verifican que `raw` no cambie durante el proceso.

Una entrega manual aprobada se registra sin alterar el archivo original:

```powershell
.\training\.venv\Scripts\python.exe scripts\register_external_datasets.py --dataset replay_attack --manual-file RUTA_EN_RAW --expected-sha256 SHA256
```

Para construir manifiestos:

```powershell
.\training\.venv\Scripts\python.exe scripts\build_external_manifests.py --input METADATA.parquet --modality pad
.\training\.venv\Scripts\python.exe scripts\build_external_manifests.py --input TECLADO.parquet --modality keyboard --dataset cmu_keystroke
.\training\.venv\Scripts\python.exe scripts\build_external_manifests.py --input MOUSE.parquet --modality mouse --dataset balabit_mouse
```

Para validar protocolos y producir comparaciones solo con resultados reales:

```powershell
.\training\.venv\Scripts\python.exe scripts\run_cross_dataset_pad.py
.\training\.venv\Scripts\python.exe scripts\run_external_behavioral_benchmarks.py
.\training\.venv\Scripts\python.exe scripts\compare_training_strategies.py
.\training\.venv\Scripts\python.exe scripts\generate_production_readiness_report.py
```

## Privacidad conductual

El esquema procesado de teclado conserva tiempos, índices, sesión, sujeto y
etiqueta legítima. No persiste tecla, carácter, ASCII, código, texto, contraseña,
palabra o frase. Para CMU, los nombres de features que contienen la identidad de
la tecla se transforman en eventos temporales sin copiar esos nombres.

El esquema de mouse conserva tiempos, coordenadas normalizadas, movimiento,
velocidad, aceleración y categorías. Descarta texto de controles, selectores CSS,
HTML y nombres de ventana.

## Integridad experimental

- Los splits oficiales se preservan.
- Todos los frames de un video permanecen en una partición.
- La extracción usa 2 FPS por defecto y admite únicamente 1–5 FPS.
- Los checksums duplicados se rechazan.
- PAD cross-dataset calibra con validation del dominio de entrenamiento, nunca
  con el test externo.
- Fine-tuning PAD usa solo `own_pad/train`.
- El modelo se selecciona con validation.
- PAD-B y PAD-C no acceden al test propio congelado sin aprobación explícita.
- ArcFace no se entrena desde cero y las plantillas de producción solo pueden
  originarse en imágenes propias, consentidas y autorizadas.

## Cierre pendiente

La fase solo podrá cerrarse experimentalmente cuando se obtengan las aprobaciones,
se registren checksums, se construyan manifiestos con datos reales y se ejecuten
los benchmarks. Los datasets públicos reducen riesgo, pero no sustituyen la prueba
propia con cámaras, equipos, operadores y ataques de la empresa.
