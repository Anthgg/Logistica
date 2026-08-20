# F005.4 — Testing Strategy

## Backend Tests

Los tests del backend geocoding ya existen y cubren:

| Archivo | Cobertura |
|---------|-----------|
| `test_logistics_geocoding.py` (35KB) | Flujos completos: search + reverse vía HTTP, autenticación, CSRF, permisos |
| `test_geocoding_api.py` (23KB) | Endpoints individualmente: validación de request/response |
| `test_geocoding_provider.py` (19KB) | `NominatimGeocodingProvider`: rate limiter, cache, errores |
| `test_geocoding_adversarial_stress.py` (11KB) | Stress: concurrencia, payloads extremos, timeouts |

**Resultado**: 91 tests pasan, 0 fallos.

### Ejecutar tests del backend

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/test_logistics_geocoding.py tests/test_geocoding_api.py tests/test_geocoding_provider.py -x -q
```

## Frontend Tests

| Archivo | Descripción |
|---------|-------------|
| `src/api/geocoding-api.test.ts` | Helpers de conversión de coordenadas WGS84↔MapLibre |
| `src/components/logistics/LocationPicker.test.tsx` | 18 casos: search, multi-candidatos, errores 503, reverse, coords manuales, disabled |
| `src/pages/test/f0054-geolocation-branch.test.tsx` | Tests de integración completa F005.4 (ya existían) |

**Resultado**: Todos los tests pasan.

### Mock global de maplibre-gl

Para que todos los tests que renderizan `BranchesPage` funcionen en jsdom,
el `vite.config.ts` incluye un alias de test que reemplaza `maplibre-gl` con
`src/test/maplibre-gl-factory.ts` (exports `MockMap`, `MockMarker`, `MockNavigationControl`).

### Ejecutar tests del frontend

```bash
npm run test:run -- "src/api/geocoding-api.test.ts" "src/components/logistics/LocationPicker.test.tsx"
```

## Testing de integración manual

1. Levantar backend: `uvicorn app.main:app --reload`
2. Levantar frontend: `npm run dev`
3. Navegar a Sedes
4. Hacer clic en "Nueva sede"
5. Seleccionar UBIGEO: Miraflores, Lima
6. Ingresar dirección: "Av. Larco 1234"
7. Hacer clic en "Ubicar en mapa"
8. Verificar que el marcador aparezca en el mapa
9. Arrastrar el marcador y verificar la sugerencia de dirección inversa
10. Confirmar la sugerencia con "Usar esta dirección"
11. Guardar la sede
12. Reabrir la sede: verificar que el mapa cargue con el marcador en las coordenadas guardadas
