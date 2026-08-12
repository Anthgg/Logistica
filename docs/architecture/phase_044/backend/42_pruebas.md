# 42 — Pruebas

## Estructura

- `tests/modules/logistics/inventory/ledger/test_ledger_units.py`
  — 28 tests unitarios.
- `tests/modules/logistics/inventory/ledger/test_ledger_http.py`
  — 9 tests HTTP.
- `tests/modules/logistics/inventory/ledger/test_ledger_db.py`
  — 3 tests de DB.

Total: 40 tests pasando.

## Cobertura

- Hashing: canonicalización, Decimal, UUID, datetime, encadenado.
- Sequence: particiones, código MOV, formato.
- Position: dimension_key, estados.
- State transition: transiciones legales.
- Validation: payload válido, errores, floats, desconocidos, dups.
- Source registry: habilitación, type-flagging.
- Adaptadores: building, idempotency_key, snapshots.
- Posting: idempotencia, duplicados, payload conflictivo.
- Kardex: scope ambiguo, filtros.
- Export: jobs.
- HTTPS: endpoints retornan 200/401/403/422.
- Seguridad: un marcador de permiso rechaza de verdad al principal sin permiso.
- Payload público: rechazo recursivo de `base_quantity` y campos derivados.
- Unidades: derivación `Decimal` exacta para unidad base idéntica.
- Fuentes futuras: adaptadores definidos pero rechazados por el registry.
