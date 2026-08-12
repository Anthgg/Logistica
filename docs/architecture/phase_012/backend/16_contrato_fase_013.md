# 16 — Contrato de Frontera para la Fase 013

## Purpose
This document establishes the exact scope boundary between **Phase 012 (Standard Definition)** and **Phase 013 (Sequence Allocation & Real Numbering Rules)**.

## Implemented in Phase 012 (`IMPLEMENTADO`)
- Canonical pattern specification: `TIPO-SEDE-AÑO-CORRELATIVO` (`OC-LIM-2026-000001`).
- Domain value objects: `DocumentCodeFormatter`, `DocumentCodeParser`, `DocumentCodeValidator`, `DocumentCodeNormalizer`, `YearResolverService`.
- Database models: `DocumentCodeStandardModel`, `DocumentSiteCodeModel`, `DocumentTypeCodePolicyModel`.
- REST Endpoints: GET/POST for standard, validation, parsing, preview (unreserved), and site codes.
- Unit and integration test suite (`tests/test_logistics_phase012.py`).

## Deferred to Phase 013 (`PENDIENTE_FASE_013`)
- Real sequence tables (`DocumentSequence`).
- Atomic sequence incrementing and database locking (`SELECT ... FOR UPDATE`, advisory locks).
- Digital series and talonarios (`DocumentSeries`, `DocumentTalonario`).
- Real correlative allocation during document issuance (`AllocateDocumentNumber`).
- Handling concurrent sequence gaps and sequence recycling prevention.
