# Architecture Documentation — Phase 013 (Backend): Digital Document Series & Talonarios Architecture

## 1. Overview
This directory contains the complete technical architecture and specification for **Phase 013 — Diseñar e implementar series y talonarios digitales** in **Proyecto T1**.

The system manages unique document sequence spaces for the scope:
$$\text{organization\_id} + \text{document\_type\_id} + \text{document\_site\_code\_id} + \text{document\_year}$$

---

## 2. Document Index
1. `README.md` — Scope and index
2. `01_auditoria_numeracion_existente.md` — Audit of legacy sequences
3. `02_modelo_series.md` — DocumentSeriesModel domain & rules
4. `03_modelo_talonarios.md` — DocumentTalonarioModel domain & rules
5. `04_modelo_numeros.md` — DocumentNumberModel ledger domain & rules
6. `05_control_concurrencia.md` — SELECT FOR UPDATE row locking & concurrency control
7. `06_idempotencia.md` — Idempotency key hashing and replay engine
8. `07_reserva_individual.md` — Internal transactional number reservation service
9. `08_reserva_rangos.md` — Range reservation & bulk talonario creation
10. `09_anulacion_no_reutilizacion.md` — Cancellation and strict non-recycling policy
11. `10_agotamiento_cambio_ano.md` — Sequence exhaustion (999,999) & annual rollover
12. `11_manifiesto_exportacion.md` — JSON manifest specification
13. `12_endpoints.md` — REST API endpoints specification
14. `13_permisos_step_up.md` — RBAC permissions & step-up security
15. `14_auditoria.md` — Immutable audit events
16. `15_migracion.md` — Alembic database migration details (`d330640013dc`)
17. `16_pruebas_concurrencia.md` — PostgreSQL concurrency test scenarios
18. `17_pruebas_generales.md` — Unit and integration testing results
19. `18_contrato_fase_014.md` — Boundary contract for Phase 014 (Document Rendering)
20. `19_contrato_fase_020.md` — Boundary contract for Phase 020 (Downloads & Reprints)
21. `20_decisiones_pendientes.md` — Backlog & pending business decisions
22. `phase_013_backend_manifest.json` — Machine-readable Phase 013 manifest
