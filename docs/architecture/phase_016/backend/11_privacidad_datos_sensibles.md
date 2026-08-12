# 11 — Privacidad de Datos Sensibles

## Política de Enmascaramiento en CPV

El documento CPV captura datos personales del conductor (DNI y número de licencia de conducir). Estos datos son **sensibles** y nunca deben aparecer en claro en los PDFs generados.

## Función `mask_sensitive_id`

```python
def mask_sensitive_id(val: str | None, visible_end: int = 2) -> str:
    if not val:
        return "******"
    clean = str(val).strip()
    if len(clean) <= visible_end:
        return "*" * len(clean)
    return "*" * (len(clean) - visible_end) + clean[-visible_end:]
```

## Ejemplos

| Valor Real | Resultado Enmascarado |
|---|---|
| `"12345642"` | `"******42"` |
| `"Q49876521"` | `"*******21"` |
| `None` | `"******"` |
| `"AB"` | `"**"` |

## Flujo de Enmascaramiento

1. El payload del request incluye `driver_dni_raw` y `driver_license_raw`.
2. En `InboundRenderingService.render_inbound_preview()`, al detectar `doc_type == "CPV"`:
   - Se construye `InboundCpvContext(**data)`
   - Se llama `cpv_ctx.get_masked_context()` que aplica masking y **elimina** los campos `_raw` del dict
3. El contexto enmascarado se pasa a `DocumentRenderCommand.document_data`
4. Jinja2 renderiza solo los campos `driver_dni_masked` y `driver_license_masked`

## Alcance
Solo aplica al documento **CPV**. Los demás documentos de la familia INBOUND no contienen identificadores personales sensibles.

## Permiso de Lectura Sensible (Pendiente)
Para futuras integraciones donde el sistema interno necesite ver el DNI completo (ej. verificación RENIEC), se requerirá un permiso adicional `logistics.documents.sensitive_read` con step-up de autenticación. Esto queda definido en la Fase de Seguridad Avanzada.
