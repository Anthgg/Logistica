# F005.4 — Map Provider Configuration

## MapLibre GL JS

Versión instalada: ver `package.json` en logisticaf-main.

**Componente**: `src/components/logistics/LocationMap.tsx`

## Configuración de tiles

El estilo del mapa se resuelve en este orden:

1. `VITE_MAP_STYLE_URL` (variable de entorno Vite)
2. Prop `styleUrl` del componente
3. Fallback: tiles OSM raster integrados

### Cambiar de proveedor de tiles

Solo actualizar `VITE_MAP_STYLE_URL` en el archivo `.env.*`:

```bash
# MapTiler (requiere API key)
VITE_MAP_STYLE_URL=https://api.maptiler.com/maps/streets/style.json?key=TU_KEY

# Stadia Maps (requiere registro)
VITE_MAP_STYLE_URL=https://tiles.stadiamaps.com/styles/alidade_smooth.json

# OSM default (sin costo, sin key)
# No definir la variable = usa tiles OSM directamente
```

**NO requiere** cambiar `LocationMap.tsx`, `LocationPicker.tsx`, ni `BranchesPage.tsx`.

## Atribución

La atribución de OpenStreetMap siempre es visible cuando se usan tiles OSM.
MapLibre GL JS muestra atribución por defecto.

No ocultar la atribución — es requerimiento de la licencia ODbL de OpenStreetMap.

## Coordinadas: convención

MapLibre GL JS usa `[longitude, latitude]` — **opuesto** al estándar WGS84 `[latitude, longitude]`.

Los helpers en `src/api/geocoding-api.ts` gestionan la conversión:

```typescript
wgs84ToMapLibreLngLat(lat, lon) // → [lon, lat] para MapLibre
mapLibreLngLatToWgs84(lngLat)   // → [lat, lon] para almacenar
```

Todos los datos persistidos usan WGS84 (`latitude`, `longitude` por separado).

## Soporte mobile

- Mapa 100% ancho en pantallas pequeñas
- Controles touch nativos de MapLibre GL JS
- Sin overflow horizontal

## Modo offline / degradado

Si MapLibre no puede cargar:
- Se muestra un error no obstructivo dentro del contenedor del mapa
- El usuario puede igualmente ingresar dirección y coordenadas manualmente
- El formulario puede guardarse sin mapa
