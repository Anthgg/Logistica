# Fase 036 — Avisos de llegada y programación de recepción

Esta carpeta define el contrato backend de la Fase 036. La implementación cubre avisos de llegada basados en órdenes de compra emitidas, revisiones inmutables, asignación de cantidades esperadas, datos declarados de transporte, calendarios, disponibilidad, holds, citas, CIT, paquetes, outbox y jobs persistentes.

El límite es deliberado: esta fase no registra llegada física, check-in, muelle, descarga, recepción, pallets físicos, lotes, series ni movimientos de inventario. Tampoco modifica el frontend ni inicia la Fase 037.

Fuente ejecutable principal: `app/modules/logistics/inbound`. Migración: `y360110036dc`. Pruebas: `tests/test_logistics_phase036.py`.

