# Fase 004 — Organización, Sedes y Almacenes

## Objetivo
Implementar la jerarquía organizacional: Organization → Branch → Warehouse.

## Alcance
- Modelos SQLAlchemy: `Organization`, `Branch`, extensión de `Warehouse`.
- Esquemas Pydantic para creación, actualización, respuesta y listado.
- Repositorios con validaciones jerárquicas.
- Servicios con reglas de integridad y estados.
- Endpoints administrativos bajo `/api/logistics/`.
- Migración Alembic reversible.
- Pruebas de integración (13 tests).

## Resultado
- **IMPLEMENTADO**: Modelos, schemas, repos, servicios, endpoints, migración.
- **COMPROBADO**: 26/26 pruebas pasan (13 Phase 003 + 13 Phase 004).
- **DOCUMENTADO**: 13 archivos + manifiesto.

## Estado
**COMPLETADO** — Listo para Fase 005.