# F005.4 — Geolocalización de Sedes

Implementación de forward/reverse geocoding, mapa interactivo MapLibre GL JS y
selección de coordenadas WGS84 en el formulario de Branch/Sede.

## Estado

- **SCHEMA_CHANGE_REQUIRED**: FALSE (reusa `Branch.address_text`, `Branch.latitude`,
  `Branch.longitude`, `Branch.ubigeo_code`)
- **ALEMBIC_HEAD**: `jl480110048dk` (sin cambios)
- **BACKEND**: Completo — módulo `geocoding/` implementado
- **FRONTEND**: `LocationMap`, `LocationPicker`, integración en `BranchesPage`

## Documentos

| Archivo | Descripción |
|---------|-------------|
| [architecture.md](./architecture.md) | Arquitectura del sistema |
| [geocoding-provider.md](./geocoding-provider.md) | Abstracción GeocodingProvider |
| [map-provider.md](./map-provider.md) | Configuración de tiles y MapLibre |
| [security.md](./security.md) | Controles de seguridad |
| [testing.md](./testing.md) | Estrategia de pruebas |
| [closeout.md](./closeout.md) | Reporte final |

## Variables de entorno

### Backend

| Variable | Defecto | Descripción |
|----------|---------|-------------|
| `GEOCODING_PROVIDER` | `nominatim` | Proveedor de geocoding |
| `NOMINATIM_BASE_URL` | `https://nominatim.openstreetmap.org` | URL base Nominatim |
| `NOMINATIM_USER_AGENT` | `LogisticaT1-BranchLocator/1.0` | User-Agent requerido |
| `NOMINATIM_TIMEOUT_SECONDS` | `5.0` | Timeout de requests |
| `NOMINATIM_MIN_INTERVAL_SECONDS` | `1.0` | Throttling mínimo |
| `GEOCODING_CACHE_TTL_SECONDS` | `3600` | TTL de caché en memoria |
| `GEOCODING_CACHE_MAX_ENTRIES` | `1000` | Máximo de entradas en caché |

### Frontend

| Variable | Descripción |
|----------|-------------|
| `VITE_MAP_STYLE_URL` | URL del estilo MapLibre (opcional, por defecto: tiles OSM) |

## Reutilización futura

Diseñado para consumo posterior por:
- RRHH / sitios de trabajo
- Geocercas de asistencia
- Orígenes y destinos de transporte
- Almacenes externos
- Rutas y seguimiento
