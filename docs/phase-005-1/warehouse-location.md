# Ubicación de almacén — estrategia B (derivación transitoria)

## El problema

El formulario de almacén pedía distrito, provincia y departamento como texto libre.
Nada los ataba a la sede a la que el almacén pertenece: una sede en Lima podía tener un
almacén declarando Arequipa. El dato quedaba internamente contradictorio y nadie se
enteraba.

## La decisión

Ante la elección entre exigir UBIGEO propio al almacén o derivarlo de la sede, el
usuario eligió **B**: derivación transitoria.

## Cómo funciona

`OrganizationService._resolve_location`:

```python
if branch.ubigeo_code:
    district = GeographyService.resolve_ubigeo(db, branch.ubigeo_code)
    if district is not None:
        return (district.district_name, district.province_name,
                district.department_name)
return data.district, data.province, data.department
```

- Si la sede tiene `ubigeo_code` (F004.5), el almacén hereda distrito, provincia y
  departamento resueltos contra `geo_districts`. No hay forma de contradecirla.
- Si la sede **no** lo tiene todavía —sedes anteriores a F004.5—, se conserva lo que
  venga en la petición. Por eso «transitoria»: el respaldo desaparece cuando todas las
  sedes estén normalizadas.

Los tres campos pasaron a opcionales en `LogisticsWarehouseCreate` precisamente porque
en el caso normal ya no los envía nadie.

## Frontend

Los inputs de distrito, provincia y departamento se eliminaron del árbol de
`WarehousesPage` —no se ocultaron con CSS ni se deshabilitaron—. En su lugar se muestra
la ubicación heredada:

- `branch.ubigeo.formatted` cuando la sede está normalizada.
- «Pendiente de normalización UBIGEO» cuando no lo está.

El segundo mensaje es información real para el usuario: le dice que la sede tiene un
dato incompleto, en vez de presentarle un hueco sin explicación.

## Qué queda abierto

La derivación es transitoria por diseño. Cerrarla requiere que todas las sedes tengan
`ubigeo_code`, lo que a su vez requiere una decisión de datos sobre las sedes heredadas.
No está autorizado todavía.
