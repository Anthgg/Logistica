# MOV — Movimiento de Almacén (Phase 017)

## Propósito
Documentar traslados internos de mercadería entre ubicaciones del mismo almacén.

## Tipos de Movimiento
- **INTERNAL_TRANSFER**: Reubicaciones operativas.
- **STATUS_CHANGE**: Cambios en el estado del stock (ej. Disponible a Cuarentena).
- **REVERSAL**: Movimiento compensatorio para anulación de transacciones erróneas.

## Elementos de Control
- **Ruta de Movimiento**: Origen → Destino visual con estados del stock asociados.
- **Detalle de Items**: SKU, descripción, lote, unidad logística y cantidad.
- **Trazabilidad**: Firma del operario que ejecutó y el supervisor que autorizó.
