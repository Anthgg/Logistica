# 02 — Arquitectura del libro de inventario

## Vista de capas

```
┌─────────────────────────────────────────────────────────────────────┐
│ Presentation (FastAPI)                                              │
│   /inventory/movements, /inventory/kardex, /inventory/ledger/...   │
│   Schemas Pydantic, dependencias locales, RBAC, Step-up, CSRF       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ Application Services                                                │
│   InventoryMovementPostingService (append-only, transactional)      │
│   InventoryMovementValidationService                                │
│   InventoryMovementCompensationService                              │
│   InventoryKardexQueryService                                        │
│   InventoryKardexRunningQuantityService                              │
│   InventoryBalancePreparationService (Fase 045)                   │
│   InventoryTraceabilityPreparationService (Fase 046)               │
│   InventoryLedgerIntegrityService                                   │
│   InventoryLedgerCheckpointService                                  │
│   InventoryLedgerReconciliationService                              │
│   InventoryLedgerExportService                                      │
│   InventoryMovementSnapshotProvider                                 │
│   PreparedInventoryEventIngestionService                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ Domain                                                              │
│   Hash service (canonical JSON, SHA-256 encadenado)                 │
│   Sequence + Code services (particiones transaccionales, MOV)       │
│   Position service (dimensión determinista, no saldo)                │
│   Availability provider (source-backed, Phase 045 reemplazará)       │
│   Idempotency service (Phase 013 IdempotencyRecordModel)             │
│   Source registry (adaptadores activos y disabled)                  │
│   State transition policy (cantidad preservada)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│ Infrastructure                                                     │
│   ORM models (13 tablas, migración gg440110044dc)                   │
│   Source adapters (Quality, Putaway, futuros)                       │
│   Jobs (ingest, retry, outbox, verify, checkpoint, reconcile)       │
└─────────────────────────────────────────────────────────────────────┘
```

## Principios

1. **Append-only absoluto**: todo `InventoryMovement` publicado es inmutable.
2. **Cantidad siempre positiva**: el sentido lo lleva `quantity_direction`.
3. **Decimal obligatorio**: nunca `float` en cantidades.
4. **Hash encadenado**: `previous_movement_hash` referencia al inmediato anterior.
5. **Idempotencia por source event**: mismo `(organization, source_system,
   source_event_type, source_event_id, source_event_version)` siempre devuelve
   el mismo posting request.
6. **Secuencia transaccional**: `SELECT FOR UPDATE` sobre
   `inventory_ledger_partitions`.
7. **Compensación, no edición**: toda corrección es un nuevo MOV que
   referencia el original.
