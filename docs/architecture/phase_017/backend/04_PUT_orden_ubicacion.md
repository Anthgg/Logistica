# PUT — Orden de Ubicación (Phase 017)

## Propósito
Guiar al operario en el traslado de mercadería aceptada desde la zona de recepción temporal hasta la ubicación de almacenamiento sugerida.

## Campos Clave
- **Ubicación de Origen**: Zona de recepción o pulmón temporal.
- **Ubicación Sugerida**: Ubicación calculada por lógica de afinidad o rotación (PENDING_PHASE_043).
- **Referencia NI / AREC**: Trazabilidad con el ingreso físico de la mercadería.
- **Datos de Trazabilidad del Producto**: SKU, Lote, Serie y Unidad Logística.

## Límites Operativos (Phase 017)
- No se ejecutan movimientos de inventario en base de datos.
- La confirmación real del putaway y el cálculo dinámico de sugerencia se implementará en la **Fase 043**.
