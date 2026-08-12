# 25 — Métricas de Observabilidad y Alertas

## 1. Métricas Prometeus / OpenTelemetry

| Nombre de Métrica | Tipo | Etiquetas (Labels) | Descripción |
| :--- | :--- | :--- | :--- |
| `ruc_lookup_requests_total` | Counter | `status`, `cache_hit` | Conteo total de consultas de RUC. |
| `ruc_lookup_latency_seconds` | Histogram | `source_type` | Latencia de resolución de consultas (P50, P95, P99). |
| `ruc_import_rows_ingested_total` | Counter | `dataset_type` | Total de filas procesadas durante ingesta. |
| `ruc_import_duration_seconds` | Gauge | `dataset_type` | Duración del proceso completo de importación. |
| `ruc_dataset_active_age_days` | Gauge | `source_code` | Antigüedad en días del dataset actualmente activo. |

---

## 2. Reglas de Alerta Crítica

1. **`RucDatasetStaleCritical`**: Se dispara si `ruc_dataset_active_age_days > 60`. Severidad: `WARNING`.
2. **`RucImportAnomalyAborted`**: Se dispara inmediatamente al registrar un evento `RUC_ANOMALY_DETECTED`. Severidad: `CRITICAL`.
3. **`RucProviderHighFailureRate`**: Se dispara si el proveedor API falla más del 15% de las peticiones en 5 minutos. Severidad: `ERROR`.
