# 12 — Observabilidad, Monitoreo y Alertas

## Dashboards y Alertas en Cloud Monitoring

| Alerta / Métrico | Umbral Crítico | Canal de Notificación | Acción Automatizada |
| :--- | :--- | :--- | :--- |
| **Error Rate (HTTP 5xx)** | $> 2.0\%$ en 5 min | Email / Slack DevOps | Notificación y pausa de CD |
| **Latencia P95** | $> 1200 \text{ ms}$ en 5 min | Email / Slack DevOps | Ingesta de métricas |
| **Uso de Memoria RAM** | $> 85\%$ en instancia | Email DevOps | Auto-escalado de contenedor |
| **Conexiones PostgreSQL** | $> 80\%$ del pool | Slack DevOps | Escalado de pool |
| **Presupuesto Mensual** | $> 80\%$ del límite pactado | Email Administrador | Notificación de costes |
