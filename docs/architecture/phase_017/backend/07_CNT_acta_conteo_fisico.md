# CNT — Acta de Conteo Físico (Phase 017)

## Propósito
Registrar los conteos de inventario programados o cíclicos para auditoría de stock.

## Protección de Conteo Ciego (Blind Count)
- **Modo Activo (`blind_count_mode=True`)**: El backend remueve por completo el campo `expected_quantity` (teórico) de las líneas de conteo enviadas al template.
- Esto evita que el operario conozca el stock esperado del sistema, forzando un conteo físico real y honesto.
- El aviso visual de conteo ciego se muestra dinámicamente en el reporte.

## Estructura del Documento
- **Equipo de Conteo**: Registro del supervisor, auditores y contadores por zona.
- **Líneas**: Soporte para primer conteo, reconteo (en caso de discrepancias) y cantidad final consensuada.
