# 45 — Runbook: gap de secuencia

## Síntoma

- `InventoryLedgerIntegrityService.verify_partition` retorna
  `GAPS_DETECTED`.

## Causa

- Una partición tiene `ledger_sequence` no monotónico.

## Acción

1. Identificar la partición y la secuencia ausente.
2. Investigar transacciones revertidas.
3. Si la transacción original fue válida, crear un movimiento
   `SYSTEM_CORRECTION` de auditoría.
4. Nunca reutilizar números.
