# 11 — Migración de Base de Datos (Alembic)

## Tablas de Seguridad Step-Up
* `step_up_challenges`: Registro del ciclo de vida de los desafíos.
* `step_up_challenge_factors`: Factores evaluados.
* `step_up_proofs`: Pruebas de un solo uso.
* `risk_evaluations`: Histórico inmutable de decisiones de riesgo.

## Índices de Alto Rendimiento
* `idx_step_up_challenges_user_status`: `(user_id, status, expires_at)`
* `idx_step_up_proofs_lookup`: `(id, session_id, permission_code, status, expires_at)`
