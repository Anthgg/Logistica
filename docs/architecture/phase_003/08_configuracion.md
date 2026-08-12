# 08. Configuración

## Variables futuras (no asignadas todavía)

| Variable | Descripción | Tipo |
|----------|-------------|------|
| `LOGISTICS_ENABLED` | Activar/desactivar el dominio logístico | bool |
| `DOCUMENT_STORAGE_PROVIDER` | Proveedor de almacenamiento de documentos | str |
| `DOCUMENT_STORAGE_BUCKET` | Bucket/path para documentos | str |
| `ROUTE_PROVIDER` | Proveedor de cálculo de rutas | str |
| `GEOCODING_PROVIDER` | Proveedor de geocodificación | str |
| `ROUTE_REQUEST_TIMEOUT` | Timeout para solicitudes de ruta | int |
| `FILE_MAX_SIZE_MB` | Tamaño máximo de archivos | int |
| `FILE_ALLOWED_MIME_TYPES` | Tipos MIME permitidos | str |
| `AUDIT_ENABLED` | Activar/desactivar auditoría logística | bool |

## Secretos

Ningún secreto se agrega al repositorio. Los tokens de proveedores externos se gestionarán via variables de entorno en Cloud Run cuando se implementen.

## Proveedores pendientes

- OSRM / openrouteservice / Mapbox — rutas
- Google Cloud Storage / S3 — archivos
- SUNAT / SUNARP / MTC — integraciones
- Twilio / SNS — SMS/OTP

Ninguno está configurado en esta fase.