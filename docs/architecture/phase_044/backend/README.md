# Phase 044 — Inventory Ledger (Append-Only Book)

## Resumen ejecutivo

La **Fase 044** entrega el **libro de inventario** del proyecto T1. Es un registro
inmutable de hechos de inventario materializados a través de **movimientos MOV** que
se encadenan mediante hashes SHA-256 deterministicos. Los movimientos pueden ser
entradas, salidas, traslados, reservas, cambios de estado/calidad, compensaciones y
operaciones reservadas para las fases 045, 047, 049 y 050.

El libro se construye como **fuente única de verdad** del inventario. La Fase 045
(saldos) y la Fase 046 (trazabilidad) consumirán este libro como única fuente.

## Componentes principales

| Capa | Ubicación | Descripción |
|------|-----------|-------------|
| Domain — value objects | `app/modules/logistics/inventory/ledger/domain/value_objects/` | Enums de familias, tipos, estados, fronteras externas, status |
| Domain — services | `app/modules/logistics/inventory/ledger/domain/services/` | Hash, sequence, position, availability, idempotency, source registry |
| Domain — policies | `app/modules/logistics/inventory/ledger/domain/policies/` | State transition policy |
| Application — commands | `app/modules/logistics/inventory/ledger/application/commands/` | Comandos del libro |
| Application — queries | `app/modules/logistics/inventory/ledger/application/queries/` | Kardex, saldo técnico, detalle |
| Application — services | `app/modules/logistics/inventory/ledger/application/services/` | Posting, validation, compensation, preparation, integrity, export |
| Infrastructure — persistence | `app/modules/logistics/inventory/ledger/infrastructure/persistence/` | ORM models (13 tablas) |
| Infrastructure — source adapters | `app/modules/logistics/inventory/ledger/infrastructure/source_adapters/` | Adaptadores Fase 042/043 |
| Infrastructure — jobs | `app/modules/logistics/inventory/ledger/infrastructure/jobs/` | Jobs persistentes |
| Presentation | `app/modules/logistics/inventory/ledger/presentation/` | Router FastAPI, schemas, dependencias locales |

## Cómo arrancar

1. Revisar y ejecutar hasta el head Alembic `gh440210044mg` (el merge incluye
   `gg440110044dc` y conserva la rama de reparación desplegada).
2. Cargar adaptadores en el bootstrap (ya cableados a través de
   `app.modules.logistics.router._create_logistics_router`)
3. Configurar las capacidades en `app.modules.logistics.rbac.permission_catalog`
4. Activar jobs en el runner persistente (`ingest_quality_events`,
   `ingest_putaway_events`, `process_outbox`, `verify_chain`, etc.)

## Pruebas

```bash
pytest tests/modules/logistics/inventory/ledger -v
```

40 tests cubren hash, validation, sequence, position, source adapters, posting,
idempotency, kardex, exports, compensation, integrity, reconciliation.

## Documentos de la fase

Los detalles se encuentran en los siguientes documentos:

- `01_auditoria_inventario_existente.md` — auditoría y hallazgos sobre el inventario
  pre-existente.
- `02_arquitectura_ledger.md` — arquitectura modular.
- `03_limites_fases_045_046_047_048_049.md` — contratos hacia fases futuras.
- `04_modelo_movimiento.md` — modelo `InventoryMovement`.
- `05_solicitudes_publicacion.md` — `InventoryMovementPostingRequest`.
- `06_familias_tipos.md` — familias y tipos de movimiento.
- `07_lineas_movimiento.md` — líneas de movimiento.
- `08_posiciones_inventario.md` — `InventoryPosition`.
- `09_fronteras_externas.md` — `InventoryExternalBoundary`.
- `10_transiciones_estado.md` — `InventoryStateTransitionPolicy`.
- `11_movimientos_balanceados.md` — balance conceptual doble efecto.
- `12_secuencias_codigos_MOV.md` — particiones y códigos.
- `13_fuentes_adaptadores.md` — `InventoryMovementSourceRegistry`.
- `14_integracion_fase_042.md` — materialización de eventos de calidad.
- `15_integracion_fase_043.md` — materialización de putaway.
- `16_reservas_futuras.md` — contratos de reserva.
- `17_ajustes_futuros.md` — contratos de ajuste.
- `18_conteos_futuros.md` — contratos de conteo.
- `19_transferencias_futuras.md` — contratos de transferencia.
- `20_validacion.md` — `InventoryMovementValidationService`.
- `21_cantidades_unidades.md` — reglas de Decimal.
- `22_disponibilidad_transitoria.md` — `InventoryAvailabilityProvider`.
- `23_publicacion_transaccional.md` — flujo de posting.
- `24_compensaciones.md` — `InventoryMovementCompensationService`.
- `25_hash_encadenado.md` — `InventoryLedgerHashChainService`.
- `26_checkpoints.md` — `InventoryLedgerCheckpoint`.
- `27_snapshot.md` — `InventoryMovementSnapshotProvider`.
- `28_kardex_tecnico.md` — `InventoryKardexQueryService`.
- `29_saldo_corrido_tecnico.md` — saldo corrido TÉCNICAL_REPLAY.
- `30_exportaciones.md` — `InventoryKardexExportJob`.
- `31_reconciliacion.md` — `InventoryLedgerReconciliationService`.
- `32_preparacion_fase_045.md` — preparación para saldos.
- `33_preparacion_fase_046.md` — preparación para trazabilidad.
- `34_eventos_dominio.md` — eventos publicados.
- `35_endpoints.md` — endpoints HTTP.
- `36_permisos_step_up.md` — RBAC y step-up.
- `37_separacion_funciones.md` — separación de funciones.
- `38_auditoria.md` — auditoría.
- `39_concurrencia_idempotencia.md` — concurrencia e idempotencia.
- `40_jobs.md` — jobs persistentes.
- `41_migracion.md` — migración Alembic.
- `42_pruebas.md` — pruebas.
- `43_rendimiento.md` — consideraciones de rendimiento.
- `44_runbook_evento_duplicado.md` — runbook.
- `45_runbook_gap_secuencia.md` — runbook.
- `46_runbook_hash_invalido.md` — runbook.
- `47_runbook_compensacion.md` — runbook.
- `48_runbook_reconciliacion.md` — runbook.
- `49_decisiones_pendientes.md` — decisiones pendientes.
- `50_auditoria_codigo_muerto_grafo.md` — análisis reproducible de los 411
  candidatos de grado cero del grafo.

## Cierre de la fase

La Fase 044 implementa el contrato backend: libro append-only, posting
transaccional, fuentes reales, hash encadenado, kardex técnico, compensaciones,
preparación para Fase 045 y 046, jobs, migración, RBAC, step-up, separación de
funciones e idempotencia, con 40 pruebas locales pasando. La migración no se
aplicó contra producción y las metas de rendimiento a gran escala siguen
pendientes de medición; no se presentan como resultados verificados.

**No se implementa la Fase 045** (saldos definitivos) ni los flujos completos de
ajustes, conteos o transferencias. Esos quedan preparados mediante contratos
y adaptadores en estado deshabilitado.
