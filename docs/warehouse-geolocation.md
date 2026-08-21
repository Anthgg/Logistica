# Geolocalización de almacén

`warehouses` admite dos modos mutuamente excluyentes:

- `uses_branch_location = true`: `latitude` y `longitude` propias son `NULL`; la ubicación efectiva se resuelve dinámicamente desde `logistics_branches` y `location_source` es `BRANCH`.
- `uses_branch_location = false`: ambas coordenadas propias son obligatorias y `location_source` es `WAREHOUSE`.

El modelo expone `effective_latitude`, `effective_longitude` y `location_source`. Esta es la única lógica de resolución; routers y clientes consumen los campos calculados.

Create y update validan par completo, rangos WGS84 y valores finitos. Cambiar de custom a inherited limpia las dos coordenadas. La sede se obtiene de la ruta y se comprueba contra el tenant autorizado; no se acepta una organización indicada por el cliente como fuente de autoridad.

El campo `address` existente conserva la dirección o referencia del almacén. Departamento, provincia y distrito continúan derivados de la sede; no se agregó otro UBIGEO.
