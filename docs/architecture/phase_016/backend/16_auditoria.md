# 16 — Auditoría

## Event Types Registrados en Fase 016

Todos los eventos de auditoría se registran mediante `AuditService().record()` en cada endpoint antes de `db.commit()`.

| `event_type` | Endpoint | Descripción |
|---|---|---|
| `logistics.inbound_document.preview_rendered` | `/preview` | PDF generado e inlineado |
| `logistics.inbound_document.preview_downloaded` | `/pdf` | PDF descargado como adjunto |
| `logistics.inbound_document.package_manifest_created` | `/document-package/manifest` | Manifiesto de paquete generado |

## Datos Registrados en `event_metadata`

### preview_rendered / preview_downloaded
```json
{
  "document_type_code": "CIT",
  "size_bytes": 4096,
  "renderer_name": "WeasyPrint",
  "file_hash": "sha256:...",
  "preview_mode": true
}
```

### package_manifest_created
```json
{
  "included_count": 5,
  "missing_count": 1
}
```

## Principios de Auditoría
- Registro **inmutable** — no se modifica ni elimina post-commit.
- El `user_id` y `session_id` provienen del `LogisticsPrincipal` inyectado por el sistema de autenticación continua.
- Todos los registros incluyen timestamp UTC automático.
