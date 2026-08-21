# Catálogos de referencia

Fuente canónica: `backend/app/modules/logistics/organization/reference_catalogs.py`.

## Los tres catálogos

| Catálogo | Entradas | Endpoint |
|---|---:|---|
| Países (ISO 3166-1 alpha-2) | 13 | `GET /logistics/catalogs/countries` |
| Zonas horarias (IANA) | 14 | `GET /logistics/catalogs/timezones` |
| Tipos de almacén | 6 | `GET /logistics/catalogs/warehouse-types` |

`/timezones` acepta `?country_code=PE` para acotar las zonas al país elegido; el backend
siempre añade UTC.

## Por qué existen

- **País y zona horaria** eran texto libre. Nada impedía guardar `Peru`, `PERU`, `PE` y
  `Perú` como cuatro valores distintos de la misma cosa.
- **Los tipos de almacén** estaban escritos dos veces: en el validador del backend y en
  `WarehousesPage`. Dos copias de una lista divergen; es cuestión de cuándo.

## Validación

Los esquemas de `organization/schemas.py` validan `country_code` y `timezone` contra los
frozensets `COUNTRY_CODES` y `TIMEZONE_CODES`. La validación no depende de que el
frontend se porte bien: un cliente que envíe `"Perú"` recibe 422.

## Frontend

`src/api/reference-catalogs-api.ts` y `src/components/logistics/CatalogSelects.tsx`
(`CountrySelect`, `TimezoneSelect`, `WarehouseTypeSelect`).

Los tres comparten contrato: muestran el nombre humano y persisten el código canónico.
Ninguno lleva la lista embebida —ese era justamente el problema—.

`TimezoneSelect` tiene un detalle que merece nombrarse: al cambiar de país, si la zona
ya seleccionada no pertenece al catálogo filtrado, se limpia. Mantenerla dejaría el
formulario en un estado imposible (una sede en Perú con zona horaria de México) que el
usuario no vería hasta recibir el 422.

Los tres estados —cargando, error, catálogo vacío— se muestran en el propio placeholder
del `select`, y el control queda deshabilitado mientras no haya datos utilizables.
