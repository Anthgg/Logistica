# F005.4 — FINAL TECHNICAL REPORT

## Geolocalización de Sedes · Dirección + Coordenadas + Mapa Interactivo

---

## Estado General

| Indicador | Valor |
|-----------|-------|
| `FEATURE` | F005.4 |
| `STATUS` | **IMPLEMENTADO Y TESTEADO** |
| `BACKEND_BRANCH` | `feat/phase-005-4-geolocation` |
| `FRONTEND_BRANCH` | `feat/phase-005-4-geolocation` |
| `PR_BACKEND` | https://github.com/Anthgg/Logistica/pull/new/feat/phase-005-4-geolocation |
| `PR_FRONTEND` | https://github.com/Anthgg/LogisticaF/pull/new/feat/phase-005-4-geolocation |

---

## Schema

| Indicador | Valor |
|-----------|-------|
| `SCHEMA_CHANGE_REQUIRED` | `FALSE` |
| `MIGRATION_CREATED` | `FALSE` |
| `ADDRESS_FIELD` | `Branch.address_text` (String 500, nullable) |
| `LATITUDE_FIELD` | `Branch.latitude` (Numeric 10,7, nullable) |
| `LONGITUDE_FIELD` | `Branch.longitude` (Numeric 10,7, nullable) |
| `UBIGEO_FIELD` | `Branch.ubigeo_code` (String 6, FK geo_districts, nullable) |

---

## Backend

| Indicador | Valor |
|-----------|-------|
| `PROVIDER_INTERFACE` | `GeocodingProvider` (Protocol, `geocoding/base.py`) |
| `INITIAL_PROVIDER` | `NominatimGeocodingProvider` |
| `SEARCH_ENDPOINT` | `POST /api/logistics/geocoding/search` |
| `REVERSE_ENDPOINT` | `POST /api/logistics/geocoding/reverse` |
| `AUTHENTICATED` | `TRUE` (sesión requerida) |
| `PERMISSIONS` | `logistics.branches.read | .create | .update` |
| `CSRF` | `TRUE` (todos los endpoints POST) |
| `CACHE` | `GeocodingLRUCache` (LRU en proceso, TTL 3600s) |
| `THROTTLING` | `AsyncRateLimiter` (`NOMINATIM_MIN_INTERVAL_SECONDS=1.0s`) |
| `TIMEOUT` | `NOMINATIM_TIMEOUT_SECONDS=5.0s` |
| `DIRECT_BROWSER_PROVIDER_CALLS` | `0` |

---

## Frontend

| Indicador | Valor |
|-----------|-------|
| `MAP_LIBRARY` | `MapLibre GL JS` |
| `MAP_STYLE_SOURCE` | `VITE_MAP_STYLE_URL` env var (fallback: OSM raster) |
| `DRAGGABLE_MARKER` | `PASS` |
| `CLICK_TO_POSITION` | `PASS` |
| `BROWSER_GEOLOCATION` | `PASS` (one-shot `getCurrentPosition`) |
| `MANUAL_COORDINATES` | `PASS` |
| `REVERSE_GEOCODING_SUGGESTION` | `PASS` (banner "Usar esta dirección") |
| `GEOCODING_PER_KEYSTROKE` | `0` (búsqueda explícita por botón) |

---

## Reusabilidad

| Indicador | Valor |
|-----------|-------|
| `WAREHOUSE_LOCATION_DUPLICATION` | `0` |
| `WAREHOUSE_STRATEGY` | `TRANSITIONAL_DERIVATION` (hereda de Branch) |
| `HR_REUSABLE` | `TRUE` (`LocationPicker` no está acoplado a Branch) |
| `TRANSPORT_REUSABLE` | `TRUE` |
| `GUESSED_COORDINATES` | `0` |

---

## Tests

### Backend
| Archivo | Tests |
|---------|-------|
| `test_logistics_geocoding.py` | ✅ integración E2E |
| `test_geocoding_api.py` | ✅ endpoints HTTP |
| `test_geocoding_provider.py` | ✅ proveedor + rate limiter + caché |
| `test_geocoding_adversarial_stress.py` | ✅ stress / adversarial |
| **Total** | **91 tests PASS** |

### Frontend
| Archivo | Tests |
|---------|-------|
| `geocoding-api.test.ts` | ✅ helpers de conversión |
| `LocationPicker.test.tsx` | ✅ 18 casos |
| `f0054-geolocation-branch.test.tsx` | ✅ Tier 1-4 completo |
| `contract-audit.test.ts` | ✅ 988 endpoints registrados |
| **Total** | **761 tests PASS, 0 fallos** |

---

## Archivos Creados / Modificados

### Backend (`Anthgg/Logistica`)
- `backend/app/modules/logistics/geocoding/__init__.py` **[NEW]**
- `backend/app/modules/logistics/geocoding/base.py` **[NEW]** — `GeocodingProvider` Protocol
- `backend/app/modules/logistics/geocoding/cache.py` **[NEW]** — `GeocodingLRUCache`
- `backend/app/modules/logistics/geocoding/rate_limiter.py` **[NEW]** — `AsyncRateLimiter`
- `backend/app/modules/logistics/geocoding/exceptions.py` **[NEW]**
- `backend/app/modules/logistics/geocoding/providers/nominatim.py` **[NEW]**
- `backend/app/modules/logistics/geocoding/router.py` **[NEW]**
- `backend/app/modules/logistics/geocoding/schemas.py` **[NEW]**
- `backend/app/modules/logistics/geocoding/service.py` **[NEW]**
- `backend/app/core/config.py` **[MODIFIED]** — 7 variables de configuración
- `backend/app/modules/logistics/router.py` **[MODIFIED]** — registro del router geocoding
- `backend/tests/test_logistics_geocoding.py` **[NEW]**
- `backend/tests/test_geocoding_api.py` **[NEW]**
- `backend/tests/test_geocoding_provider.py` **[NEW]**
- `backend/tests/test_geocoding_adversarial_stress.py` **[NEW]**
- `docs/phase-005-4/` **[NEW]** — 6 archivos de documentación

### Frontend (`Anthgg/LogisticaF`)
- `src/api/geocoding-api.ts` **[NEW]** — DTOs + helpers de conversión
- `src/components/logistics/LocationMap.tsx` **[NEW]** — mapa MapLibre GL JS
- `src/components/logistics/LocationPicker.tsx` **[NEW]** — widget dirección + mapa
- `src/pages/BranchesPage.tsx` **[MODIFIED]** — integración LocationPicker
- `src/api/geocoding-api.test.ts` **[NEW]**
- `src/components/logistics/LocationPicker.test.tsx` **[NEW]** — 18 tests
- `src/pages/test/f0054-geolocation-branch.test.tsx` **[NEW]** — Tier 1-4
- `src/test/maplibre-gl-factory.ts` **[NEW]** — mock global de maplibre-gl
- `src/test/maplibre-mock.ts` **[NEW]** — `MockMap`, `MockMarker`
- `vite.config.ts` **[MODIFIED]** — alias test maplibre-gl
- `scripts/contracts/backend-routes.phase045.json` **[MODIFIED]** — 988 ops
- `scripts/audit-api-contract.mjs` **[MODIFIED]** — SHA actualizado
- `.env.local.example` **[MODIFIED]** — `VITE_MAP_STYLE_URL`
