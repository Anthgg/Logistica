# F005.4 — Arquitectura de Geocoding y Mapa

## Visión general

```
Usuario
  │
  ▼
BranchesPage (formulario de sede)
  │
  ├─ UbigeoSelector (UBIGEO administrativo — fuente canónica)
  │
  └─ LocationPicker (dirección + mapa + coordenadas)
       │
       ├─ Input de dirección + botón "Ubicar en mapa"
       ├─ LocationMap (MapLibre GL JS — solo renderizado y eventos)
       └─ Coordinates display (editable)
            │
            ▼
       geocodingApi (src/api/geocoding-api.ts)
            │
            ▼
       Backend: POST /api/logistics/geocoding/search
       Backend: POST /api/logistics/geocoding/reverse
            │
            ▼
       GeocodingService (orchestration)
            │
            ├─ GeocodingLRUCache (caché en proceso)
            ├─ AsyncRateLimiter (throttling Nominatim)
            └─ NominatimGeocodingProvider (proveedor intercambiable)
                     │
                     ▼
              Nominatim API (openstreetmap.org)
```

## Invariantes clave

1. **El navegador nunca llama directamente a Nominatim** — todo pasa por el backend
2. **UBIGEO = divisiones administrativas oficiales** — no sustituir con OSM
3. **Coordenadas = posición geográfica estimada** — el usuario puede corregir manualmente
4. **Conversión de coordenadas explícita** — MapLibre usa `[lng, lat]`, WGS84 usa `[lat, lng]`
5. **SCHEMA_CHANGE_REQUIRED=FALSE** — se reeusan `address_text`, `latitude`, `longitude`, `ubigeo_code`
6. **Warehouse.TRANSITIONAL_DERIVATION** — hereda ubicación de Branch, no duplica

## Flujo de búsqueda

```
1. Usuario escribe dirección
2. Usuario selecciona UBIGEO (departamento → provincia → distrito)
3. Usuario hace clic en "Ubicar en mapa"
4. LocationPicker → geocodingApi.search({ address, ubigeo_code })
5. Backend: enriquece query con jerarquía UBIGEO → "Av. X, Distrito, Provincia, Dept, Perú"
6. Backend: verifica caché → si hit: retorna sin llamar Nominatim
7. Backend: aplica rate limiter (≥1s entre requests)
8. Backend: llama Nominatim con User-Agent configurado
9. Backend: normaliza respuesta en DTO propio
10. Frontend: selecciona candidato único o muestra lista para selección manual
11. LocationMap: vuela a coordenadas seleccionadas
```

## Flujo de reverse geocoding

```
1. Usuario arrastra el marcador (dragend) o hace clic en el mapa
2. LocationPicker → geocodingApi.reverse({ latitude, longitude })
3. Backend: normaliza resultado
4. Frontend: muestra "Dirección sugerida por el mapa" con botón "Usar esta dirección"
5. Solo si usuario acepta → reemplaza campo address_text
```
