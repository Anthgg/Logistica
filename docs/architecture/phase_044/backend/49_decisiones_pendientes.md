# 49 — Decisiones pendientes

1. **Catálogo documental MOV**: el `DocumentType` con code `MOV` debe
   existir en Fase 099 para evitar el fallback UUID técnico.
2. **Limpieza de modelo legacy**: `app/models/inventory_movement.py`
   debe eliminarse formalmente en una fase de limpieza.
3. **Soporte de movimientos INIT_MIGRATION**: la Fase 098 debería
   decidir si el type `MIGRATION_OPENING_ENTRY` consume
   `OPENING_BALANCE` o `TECHNICAL_COMPENSATION`.
4. **Fase 045 - Saldos**: pendiente. El `InventoryBalancePreparationService`
   consume el libro como única fuente.
5. **Fase 046 - Trazabilidad**: pendiente. El
   `InventoryTraceabilityPreparationService` entrega las observaciones.
6. **Fase 047 - Ajustes**: todavía no se aprueban movimientos sin
   step-up CRITICAL.
7. **Fase 048 - Conteos**: adaptador registrado, no habilitado.
8. **Fase 049/050 - Transferencias**: no se implementan.
9. **Audit service real**: la integración con `LogisticsAuditEvent`
   queda cableada; una fase futura debe asegurar que el proyecto
   registra todos los eventos esperados.
