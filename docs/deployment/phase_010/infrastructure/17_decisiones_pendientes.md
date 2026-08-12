# 17 — Decisiones Pendientes de Infraestructura

## Temas Pendientes de Configuración

1. **Configuración de Dominio Corporativo Personalizado:** Vinculación DNS de los dominios finales (ej: `api.andeslog.pe` y `app.andeslog.pe`) en Google Cloud DNS.
2. **Workload Identity Federation vs Service Account Keys:** Se recomienda migrar la autenticación de GitHub Actions desde claves JSON hacia Workload Identity Federation para eliminar el manejo de claves privadas estáticas.
