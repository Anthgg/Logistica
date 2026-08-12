# TRA — Orden de Transferencia (Phase 017)

## Propósito
Autorizar y planificar el traslado de mercadería entre dos almacenes diferentes de la organización (origen y destino).

## Reglas de Validación
- **Diferencia de Almacenes**: Se valida estrictamente en el esquema que `source_warehouse_name != destination_warehouse_name`.
- **Items**: Obligatoriedad de registrar SKU, lote y cantidad solicitada mayor a cero.

## Flujo Visual
Muestra una ruta de transferencia interactiva destacando el almacén de despacho y el almacén receptor, junto con los datos del transportista y vehículo asignado.
