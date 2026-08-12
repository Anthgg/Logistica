# 14 — Endpoints de la API

## Router: `inbound_documents_router`
Prefijo: `/api/logistics/inbound`  
Tags: `Logistics - Inbound Documents`

---

### POST `/api/logistics/inbound/documents/{document_type_code}/preview`
Genera y devuelve el PDF de vista previa (inline) de un documento de recepción.

**Path param:** `document_type_code` — uno de: `CIT`, `CPV`, `AREC`, `NI`, `DIF`, `NC`  
**Body:** `dict[str, Any]` con los datos del contexto documental  
**Permiso:** `logistics.documents.read`  
**Response:** `application/pdf` con marca de agua `VISTA PREVIA`  
**Headers respuesta:**
- `Content-Disposition: inline; filename="PREVIEW_CIT_..."` 
- `X-Document-Mode: PREVIEW`
- `X-Document-Type: CIT`
- `X-Content-Hash: <sha256>`

**Auditoría:** `logistics.inbound_document.preview_rendered`

---

### POST `/api/logistics/inbound/documents/{document_type_code}/pdf`
Descarga el PDF generado como archivo adjunto.

**Igual que `/preview` pero con:**
- `Content-Disposition: attachment; filename="PREVIEW_CIT_2026.pdf"`

**Auditoría:** `logistics.inbound_document.preview_downloaded`

---

### POST `/api/logistics/inbound/document-package/manifest`
Evalúa las condiciones de un evento de recepción y devuelve el manifiesto del paquete documental.

**Body:** `dict[str, Any]` con flags del evento (has_appointment, has_differences, etc.)  
**Permiso:** `logistics.documents.read`  
**Response:** `ReceptionPackageManifestResponse` (JSON)  
**Auditoría:** `logistics.inbound_document.package_manifest_created`
