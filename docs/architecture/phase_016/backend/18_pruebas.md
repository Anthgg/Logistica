# 18 — Pruebas

## Archivo: `tests/test_logistics_phase016.py`

### Resultado: **5/5 passed** (16.24s)

---

### `test_driver_privacy_masking_utility`
Verifica la función `mask_sensitive_id()` directamente:
- `"12345642"` → `"******42"` ✅
- `"Q49876521"` → `"*******21"` ✅
- `None` → `"******"` ✅

---

### `test_inbound_rendering_service_all_6_documents`
Llama a `InboundRenderingService.render_inbound_preview()` para los 6 tipos:
- **CIT:** PDF válido con `%PDF-` header, `"CIT"` en filename ✅
- **CPV:** PDF válido con masking aplicado, `"CPV"` en filename ✅
- **AREC:** PDF válido, `"AREC"` en filename ✅
- **NI:** PDF válido, `"NI"` en filename ✅
- **DIF:** PDF válido, `"DIF"` en filename ✅
- **NC:** PDF válido (familia QUALITY), `"NC"` en filename ✅

---

### `test_reception_package_manifest_rules`
Verifica las reglas del manifiesto con `has_appointment=True`, `has_differences=True`, `has_non_conformity=True`:
- `included_documents` contiene: CIT, CPV, AREC, NI, DIF, NC ✅
- `warnings` tiene al menos 1 aviso (NC requiere inspector) ✅

---

### `test_api_openapi_inbound_registered`
Verifica que el esquema OpenAPI expone los 3 endpoints:
- `/api/logistics/inbound/documents/{document_type_code}/preview` ✅
- `/api/logistics/inbound/documents/{document_type_code}/pdf` ✅
- `/api/logistics/inbound/document-package/manifest` ✅

---

### `test_api_unauthenticated_inbound_returns_401`
Verifica que sin cookie de sesión los endpoints devuelven `401 Unauthorized` ✅
