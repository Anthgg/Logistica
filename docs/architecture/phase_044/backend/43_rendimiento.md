# 43 — Rendimiento

## Índices

- `inventory_movements(organization_id)`, `(ledger_partition_key)`,
  `(ledger_sequence)`, `(movement_type)`, `(movement_family)`,
  `(source_event_id)`, `(occurred_at)`, `(posted_at)`.
- `inventory_movement_lines(inventory_movement_id)`, `(product_id)`,
  `(source_position_id)`, `(destination_position_id)`.
- `inventory_positions(organization_id)`, `(warehouse_id)`,
  `(warehouse_location_id)`, `(product_id)`, `(dimension_key)`.
- `inventory_movement_source_references(source_event_id)`,
  `(source_document_id)`.

## Paginación

- Kardex: `page + page_size` (max 500).
- Para 100M de movimientos se recomienda paginación por cursor
  `(ledger_partition_key, ledger_sequence)`.

## Objetivos pendientes de medición

Los valores siguientes son SLO propuestos, no resultados de benchmark. En esta
entrega no hubo una base local equivalente a 100M de movimientos ni ejecución
contra producción, por lo que no se fabrican métricas.

- 1k publicaciones concurrentes: < 5s p95.
- Kardex 5 años: < 2s p95.
- Verificación cadena: < 1s p95 por partición.
- Reconciliación 1M eventos: < 60s p95.
- Exportación 10M filas: < 30min p95.
