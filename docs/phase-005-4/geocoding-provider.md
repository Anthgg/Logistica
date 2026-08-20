# F005.4 — GeocodingProvider Abstraction

## Interface

El módulo `app/modules/logistics/geocoding/base.py` define:

```python
@runtime_checkable
class GeocodingProvider(Protocol):
    async def search(self, query: str, limit: int = 5) -> list[GeocodeLocationResult]: ...
    async def reverse(self, latitude: float, longitude: float) -> GeocodeLocationResult | None: ...
```

## Proveedores disponibles

### NominatimGeocodingProvider (inicial)

- **Módulo**: `providers/nominatim.py`
- **URL base**: `https://nominatim.openstreetmap.org` (configurable)
- **Política de uso**: https://operations.osmfoundation.org/policies/nominatim/
  - User-Agent identificable **obligatorio**
  - No más de 1 request/segundo desde un origen (rate limiter incorporado)
  - No usar para autocomplete por keystroke — cumplido por diseño
  - Atribución OSM visible — cumplido en frontend
- **Timeouts**: `NOMINATIM_TIMEOUT_SECONDS` (default 5s)
- **Retries**: no automáticos (un fallo → error, no loop infinito)

## Agregar un nuevo proveedor

1. Crear `providers/mi_proveedor.py` implementando `GeocodingProvider` Protocol
2. En `router.py` → `get_geocoding_service()`:
   ```python
   if settings.GEOCODING_PROVIDER == "mi_proveedor":
       provider = MiGeocodingProvider(...)
   ```
3. No modificar `BranchesPage`, `LocationPicker`, `LocationMap` ni el schema de BD

## Caché

- **Tipo**: LRU en proceso (`GeocodingLRUCache`)
- **Key search**: `sha256(query + limit)` normalizado
- **Key reverse**: coordenadas redondeadas a 4 decimales (`~11m precision`)
- **TTL**: `GEOCODING_CACHE_TTL_SECONDS` (default 3600s)
- **Max entries**: `GEOCODING_CACHE_MAX_ENTRIES` (default 1000)
- **No introduce Redis** — cache en memoria es suficiente para el volumen esperado

## Manejo de errores

| Error | HTTP | Código |
|-------|------|--------|
| Provider timeout/unreachable | 503 | `GEOCODING_PROVIDER_UNAVAILABLE` |
| Rate limit excedido | 429 | `GEOCODING_RATE_LIMIT_EXCEEDED` |
| Coordenadas inválidas | 422 | `GEOCODING_INVALID_COORDINATES` |
| Parámetros inválidos | 422 | `GEOCODING_VALIDATION_ERROR` |
