# 14 — Integración Fase 042 (`quality_quarantine`)

Se consumen:

- `QualityDispositionEventModel` (eventos de disposición).
- `InboundInventoryDispositionAllocationModel` (asignaciones).
- `QuarantineReleaseAuthorizationModel`.
- `QuarantineRejectionAuthorizationModel`.

Se materializa:

- `QUARANTINE_APPLIED`: origen = recepción/staging, destino = posición cuarentena.
- `QUARANTINE_RELEASED`: origen = cuarentena, destino = staging aprobado.
- `QUALITY_BLOCKED`: origen = cuarentena, destino = bloqueado.
- `DISPOSITION_SPLIT`: refleja la división de referencias, sin duplicar
  cantidad.

El job `ingest_quality_events` itera los `QualityDispositionEvent`
pendientes y los materializa. Cada evento se procesa **una sola vez**.
Si la integridad de origen falla, el materializador no crea el MOV.
