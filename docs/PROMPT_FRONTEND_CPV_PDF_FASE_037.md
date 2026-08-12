# Prompt para corregir el frontend React/Vite — CPV PDF (Fase 037)

Actúa como ingeniero frontend senior especializado en React, Vite y TypeScript. Trabaja únicamente en el repositorio `proyecto tesis front/frontend`; no modifiques el backend, no inventes endpoints y no hagas cambios visuales de CSS salvo que sean imprescindibles para mostrar u ocultar correctamente una acción existente.

## Objetivo

Corregir el flujo de emisión, consulta y descarga del documento CPV de Control de Puerta usando el contrato real del backend. El backend publica `API_ROOT` con el prefijo `/api` ya incluido; las rutas enviadas a `apiRequest` no deben repetir `/api`.

## Contrato backend autoritativo

### Emitir CPV

- Método: `POST`
- Ruta para `apiRequest`: `/logistics/gate-check-ins/{checkInId}/issue-document`
- URL HTTP final: `${API_ROOT}/logistics/gate-check-ins/{checkInId}/issue-document`
- Headers:
  - `X-CSRF-Token: <token>`
  - `Idempotency-Key: <uuid>`; usar exactamente este nombre, no `X-Idempotency-Key`.
- Cookies: `credentials: 'include'` — ya debe resolverlo `apiRequest`.
- Respuesta `201 application/json`:

```ts
interface GateCpvDocumentResponse {
  document_instance_id: string
  check_in_id: string
  document_code: string | null
  status: string
  issued_at: string | null
  snapshot_hash: string | null
  download_url: string
  expires_at: string | null
}
```

La operación es idempotente por recurso: si el CPV ya fue emitido, el backend devuelve el documento existente y no consume otro correlativo.

### Consultar metadatos del CPV

- Método: `GET`
- Ruta para `apiRequest`: `/logistics/gate-check-ins/{checkInId}/document`
- Respuesta `200`: `GateCpvDocumentResponse`.
- Si aún no fue emitido, el backend responde `404` con código `GATE_DOCUMENT_NOT_ISSUED`. Tratar únicamente ese `404` como `null`; no ocultar otros errores.

### Descargar PDF

- Método: `GET`
- Ruta: `${API_ROOT}/logistics/gate-check-ins/{checkInId}/document/pdf`
- Cookies: `credentials: 'include'`.
- Header: `Accept: application/pdf`.
- Respuesta `200 application/pdf` con `Content-Disposition: attachment` y `Cache-Control: private, no-store`.
- No enviar CSRF en este `GET`.
- Verificar que `content-type` incluya `application/pdf` antes de convertir a `Blob`. Si la respuesta no es PDF, extraer el error JSON cuando sea posible y lanzar un error visible; nunca descargar JSON con extensión `.pdf`.

### Vista previa

- `GET /logistics/gate-check-ins/{checkInId}/preview` devuelve JSON de vista previa, no un PDF ni un `GateControlDocument`.
- Crear un tipo separado para esta respuesta. No asumir que previsualizar crea o emite un documento.

## Cambios requeridos

1. En `src/features/gate-control/api/gateDocumentsApi.ts`:
   - Cambiar `X-Idempotency-Key` por `Idempotency-Key`.
   - Corregir `downloadDocument` para solicitar `/document/pdf`, no `/document`.
   - Mantener `API_ROOT`; no usar URLs relativas hardcodeadas ni leer `import.meta.env.VITE_API_URL` directamente.
   - Eliminar el parámetro `_documentId` si ya no tiene uso, y actualizar todos los consumidores.
   - Implementar manejo diferenciado de `404` en `getDocument`.

2. En `src/features/gate-control/types/gate-control.ts`:
   - Sustituir el tipo ficticio usado por este flujo por el contrato `GateCpvDocumentResponse`.
   - No fabricar `version`, `reprints`, `corrections_count`, `integrity_ok`, `file`, `can_preview`, `can_issue` o `can_download`: el backend no los devuelve en estas rutas.
   - Las capacidades de acciones se obtienen exclusivamente de `GateCheckInCapabilities`.

3. En `GateControlDocumentPanel.tsx` y consumidores:
   - Usar `document_instance_id`, `document_code`, `status`, `issued_at` y `snapshot_hash`.
   - Cuando no existe documento, mostrar la acción de emitir si `capabilities.can_issue_CPV` es verdadera; actualmente el botón de emisión queda inaccesible cuando `cpvDocument` es `null`.
   - Después de emitir, conservar la respuesta o volver a consultar los metadatos.
   - Para descargar, usar como nombre `${document_code ?? checkInId}.pdf` y ejecutar siempre `URL.revokeObjectURL` dentro de `finally`.
   - No mostrar como datos reales campos que el backend no publica.

4. Agregar pruebas con Vitest/MSW o mocks de `fetch` que demuestren:
   - emisión con `Idempotency-Key` y CSRF;
   - metadatos `200` correctamente tipados;
   - `404 GATE_DOCUMENT_NOT_ISSUED` convertido en `null`;
   - descarga desde `/document/pdf` con `credentials: 'include'`;
   - aceptación exclusiva de `application/pdf`;
   - rechazo de una respuesta JSON para evitar archivos PDF corruptos;
   - botón de emisión visible cuando no hay documento y la capacidad lo permite;
   - revocación del Blob URL.

5. Ejecutar y reportar:
   - pruebas específicas del módulo Gate Control;
   - `npm run typecheck` si existe;
   - `npm run lint`;
   - `npm run build`;
   - validador OpenAPI del proyecto.

## Endpoints que continúan fuera del contrato actual

No implementar ni simular estos endpoints hasta que una fase backend posterior los publique en OpenAPI:

- `POST /logistics/procurement/purchase-orders`
- `PATCH /logistics/procurement/purchase-orders/{id}`
- `GET /logistics/procurement/requisitions/stats`
- `GET /logistics/vehicle-verifications/{id}`
- `GET /logistics/vehicle-verifications/stats`
- `GET /logistics/vehicle-verifications/{id}/evidences/{evidenceId}`

Mantén esas funciones detrás de una capacidad/feature flag o con un error explícito de “no disponible en el contrato actual”. No hagas peticiones silenciosas que generen `404` y luego se oculten con `try/catch`.

## Criterios de aceptación

- Ninguna descarga de CPV consulta el endpoint JSON `/document` esperando un PDF.
- Ninguna URL empieza con `/api` dentro de `apiRequest` ni omite `API_ROOT` en un `fetch` directo.
- El header es `Idempotency-Key`.
- El frontend no inventa campos ni rutas.
- El flujo emitir → consultar → descargar funciona en producción contra Cloud Run.
- No hay cambios de backend, datos, migraciones, HTML estático ni rediseño visual.
