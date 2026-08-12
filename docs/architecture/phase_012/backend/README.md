# Architecture Documentation — Phase 012 (Backend): Document Coding Standard Architecture

## 1. Overview
This directory contains the full architecture specification for **Phase 012 — Definir el estándar de códigos documentales** in **Proyecto T1**.

The canonical code pattern established for all internal logistics documents is:
$$\text{TIPO-SEDE-AÑO-CORRELATIVO}$$
*(Example: `OC-LIM-2026-000001`)*

---

## 2. Document Index
1. `README.md` — Overview & scope
2. `01_auditoria_codigos_existentes.md` — Existing code audit
3. `02_norma_codificacion.md` — Coding standard specification
4. `03_codigo_tipo_documental.md` — TIPO segment rules
5. `04_codigo_documental_sede.md` — SEDE segment & DocumentSiteCode rules
6. `05_ano_documental.md` — AÑO segment & timezone rules
7. `06_correlativo_conceptual.md` — CORRELATIVO segment & overflow rules
8. `07_documentos_externos.md` — External document reference rules
9. `08_versionado_estandar.md` — Standard versioning (SemVer 1.0.0)
10. `09_objetos_valor.md` — Domain value objects, Formatter, Parser, Validator
11. `10_endpoints.md` — REST API endpoints documentation
12. `11_permisos.md` — RBAC permissions matrix
13. `12_auditoria.md` — Immutable audit events
14. `13_migracion.md` — Alembic database migration details
15. `14_ejemplos_aprobados.md` — Approved examples for REQ to DEV
16. `15_pruebas.md` — Testing suite & regression results
17. `16_contrato_fase_013.md` — Boundary contract for Phase 013
18. `17_decisiones_pendientes.md` — Open decisions & backlog
19. `phase_012_backend_manifest.json` — Machine-readable Phase 012 manifest
