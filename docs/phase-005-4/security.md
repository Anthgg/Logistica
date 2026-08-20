# F005.4 — Security Controls

## Authentication & Authorization

- **Todos los endpoints de geocoding requieren sesión autenticada**
- **Permisos requeridos**: `logistics.branches.read` OR `logistics.branches.create` OR `logistics.branches.update`
- **CSRF**: todos los endpoints POST verifican `verify_csrf`
- **No existen endpoints de geocoding públicos** — `UNJUSTIFIED_PUBLIC_GEOCODING_ENDPOINTS=0`

## Multi-tenancy

- Los endpoints de geocoding son geograficamente genéricos (búsqueda de dirección) y no exponen datos de un tenant específico
- Si se provee `branch_id` en contexto futuro, debe validarse que el branch pertenezca a la organización del `authenticated_principal`
- El `ubigeo_code` es resuelto por el backend contra el catálogo oficial — no se confía en nombres enviados por el frontend

## Input Validation

- `address`: min 1 char, max 500 chars, strip whitespace
- `ubigeo_code`: exactamente 6 dígitos (`^[0-9]{6}$`)
- `limit`: 1-20
- `latitude`: -90.0 ≤ lat ≤ 90.0
- `longitude`: -180.0 ≤ lon ≤ 180.0
- NaN e Infinity son rechazados por Pydantic

## Provider Isolation

- `NominatimGeocodingProvider` está encapsulado — el router no conoce detalles de Nominatim
- Timeout configurable (`NOMINATIM_TIMEOUT_SECONDS`) — evita cuelgues indefinidos
- Rate limiter (`NOMINATIM_MIN_INTERVAL_SECONDS`) — respeta política de uso
- Errores del proveedor se mapean a `503 GEOCODING_PROVIDER_UNAVAILABLE` — no expone stacktraces

## Frontend Security

- `geocoding-api.ts` nunca llama directamente a Nominatim u otras APIs de mapas externas
- Tiles de OSM se cargan directamente en el navegador (es el comportamiento estándar de MapLibre GL JS con estilo de tiles OSM)
- `VITE_MAP_STYLE_URL` permite cambiar el proveedor de tiles sin tocar código
- La atribución OSM siempre es visible — requerimiento de licencia ODbL

## Secrets

- Nominatim público no requiere API key
- `REAL_SECRET_LEAKS=0`
- No introducir variables de entorno innecesarias
