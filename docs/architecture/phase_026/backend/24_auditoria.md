# 24 — Catálogo de Eventos de Auditoría Inmutable (`logistics_audit_events`)

## Catálogo de 18 Eventos de Auditoría de la Fase 026

Todas las acciones del módulo RUC se registran de forma inmutable en el log central de auditoría:

| Evento | Categoría | Severidad | Descripción / Payload Key |
| :--- | :--- | :--- | :--- |
| `RUC_DATASET_DISCOVERED` | Ingesta | INFO | Nueva versión de padrón detectada en origen |
| `RUC_DATASET_DOWNLOAD_STARTED` | Ingesta | INFO | Inicio de descarga de archivo ZIP oficial |
| `RUC_DATASET_DOWNLOAD_COMPLETED` | Ingesta | INFO | Descarga completada y hash SHA-256 verificado |
| `RUC_DATASET_PARSED` | Ingesta | INFO | Finalización del parsing streaming de registros |
| `RUC_DATASET_ACTIVATED` | Ingesta | CRITICAL | Conmutación atómica de dataset activo en producción |
| `RUC_DATASET_ROLLED_BACK` | Ingesta | WARNING | Rollback ejecutado a versión previa SUPERSEDED |
| `RUC_DATASET_REJECTED` | Ingesta | ERROR | Dataset rechazado por fallo de formato o integridad |
| `RUC_LOOKUP_PERFORMED` | Búsqueda | INFO | Consulta de RUC realizada por usuario o sistema |
| `RUC_LOOKUP_CACHE_HIT` | Caché | DEBUG | Respuesta servida desde caché L1/L2 |
| `RUC_LOOKUP_CACHE_MISS` | Caché | DEBUG | Fallo de caché y consulta efectuada a BD |
| `RUC_ASSISTED_VERIFICATION_CREATED` | Verificación | INFO | Verificación manual asistida registrada por operador |
| `RUC_ASSISTED_VERIFICATION_APPROVED` | Verificación | NOTICE | Verificación asistida aprobada (4 ojos) |
| `RUC_PARTNER_VERIFIED` | Socio | INFO | Socio comercial verificado contra padrón |
| `RUC_CONFLICT_DETECTED` | Conflicto | WARNING | Discrepancia detectada entre socio y SUNAT |
| `RUC_CONFLICT_RESOLVED` | Conflicto | INFO | Conflicto resuelto por usuario gestor |
| `RUC_PROVIDER_FALLBACK` | Resiliencia | WARNING | Fallback activado por indisponibilidad de proveedor API |
| `RUC_ANOMALY_DETECTED` | Ingesta | ERROR | Detención de ingesta por caída >20% de filas |
| `RUC_JOB_FAILED` | Ingesta | ERROR | Fallo catastrófico en la ejecución del CLI Job |
