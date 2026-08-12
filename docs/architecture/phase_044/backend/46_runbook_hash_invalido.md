# 46 — Runbook: hash inválido

## Síntoma

- `InventoryLedgerIntegrityService.verify_partition` retorna
  `HASH_MISMATCH`.

## Causa

- El libro fue modificado o la canonicalización cambió.

## Acción

1. Bloquear postings dependientes.
2. Auditar la partición.
3. Si la modificación es legítima (migración), regenerar hash bajo
   nueva `canonicalization_version`.
4. Si es ilegítima, abrir incidente de seguridad y restaurar desde
   checkpoint.
