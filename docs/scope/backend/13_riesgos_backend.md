# 13. Matriz de Riesgos y Decisiones Pendientes — Proyecto T1

## 1. Riesgos Técnicos y Arquitecturales

| ID | Riesgo Identificado | Impacto | Probabilidad | Estrategia de Mitigación Sugerida |
|---|---|---|---|---|
| R01 | **Bloqueos por Transacciones de Stock Concurrente:** Altas peticiones simultáneas de picking sobre la misma ubicación pueden causar deadlocks en PostgreSQL. | ALTO | MEDIA | Utilizar bloqueo pesimista `SELECT FOR UPDATE` con timeout explícito y procesamiento en colas en PostgreSQL. |
| R02 | **Inestabilidad en APIs Públicas (SUNAT/MTC):** Caída o lentitud de servicios de consulta RUC o brevete de terceros. | MEDIO | ALTA | Implementar almacenamiento en caché local (padrón en PostgreSQL) y degradación grácil a ingreso manual con flag `PENDING_VERIFICATION`. |
| R03 | **Pérdida de Señal GPS en Conducción:** Puntos ciegos de cobertura móvil en carretera. | MEDIO | ALTA | La App Móvil del conductor almacenará coordenadas en SQLite local y sincronizará en ráfagas (batch) al recuperar señal. |
| R04 | **Retraso en Generación de PDFs en Cloud Run:** Sobrecarga de CPU al compilar documentos PDF síncronamente en el worker de FastAPI. | MEDIO | MEDIA | Delegar la generación de documentos PDF pesados a tareas en segundo plano (FastAPI `BackgroundTasks` o cola Celery/Cloud Tasks). |
| R05 | **Superación de Límites de Tamaño en Evidencias:** Archivos de fotos de entrega pesados subidos directamente al servidor FastAPI. | ALTO | MEDIA | Utilizar URLs firmadas (Presigned URLs) de Google Cloud Storage para que el cliente web/móvil suba la imagen directamente al Bucket. |

---

## 2. Decisiones Pendientes de Definición

- **[PENDIENTE DE DECISIÓN] Proveedor de Envío SMS/OTP:** Seleccionar entre Twilio o AWS SNS según presupuesto y tasa de entrega local en Perú.
- **[PENDIENTE DE DECISIÓN] Motor de Rutas Externo:** Determinar si se despliega una instancia propia de OSRM/Valhalla en Docker Compose o se utiliza un API comercial con cuota gratuita.
- **[PENDIENTE DE DECISIÓN] Definición de Formato de Series:** Confirmar la convención exacta de series para Guías de Remisión Internas (ejemplo: `EG01-00000001` vs `T001-00000001`).
