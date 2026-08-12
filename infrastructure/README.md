# Infraestructura local y de producción

Este directorio reúne verificaciones y notas operativas. La definición ejecutable
es `compose.yaml`; `compose.production.yaml` elimina la exposición de PostgreSQL,
exige secretos y activa las validaciones estrictas de modelos.

- `healthchecks/`: contratos de salud de cada servicio.
- `nginx/`: decisiones de seguridad del servidor del frontend.
- `postgres/`: persistencia, red y copias de seguridad.
- `scripts/`: comprobaciones automatizadas de las imágenes y montajes.

Los modelos, manifiestos y datos procesados son entradas externas de solo lectura.
Las únicas escrituras persistentes autorizadas son el volumen de PostgreSQL,
`data/captures` y `data/reports/final`.
