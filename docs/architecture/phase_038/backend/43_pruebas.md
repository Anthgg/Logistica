# 43. Pruebas

Cobertura requerida: máquinas de estado, contratos que rechazan autoridad cliente, métricas, catálogo RBAC/step-up/audit, manifest de migración, OpenAPI, doble asignación concurrente, idempotencia, separación de funciones y contrato read-only a Fase 039.

Las pruebas PostgreSQL deben usar `TEST_DATABASE_URL` aislada y `alembic upgrade head`; SQLite no reemplaza las pruebas de locks/índices parciales.

