# 14 — Decisiones Pendientes

## Puntos de Configuración e Infraestructura Pendientes

1. **Configuración de Dominio Personalizado en Cloud Run:** El servicio en producción utiliza actualmente la URL administrada por Cloud Run (`https://autenticacion-continua-api-177686674468.southamerica-west1.run.app`). La vinculación de un dominio corporativo personalizado (ej: `api.andeslog.pe`) queda pendiente de mapeo DNS.
2. **Políticas de Retención de Artefactos Docker:** Se recomienda configurar una política de limpieza automática en Artifact Registry para conservar únicamente los últimos 20 etiquetados inmutables y purgar imágenes antiguas.
