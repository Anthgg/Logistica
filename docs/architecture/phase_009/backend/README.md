# Fase 009 — Integración de Autenticación Continua con Acciones Logísticas Sensibles (Backend)

## Objetivo
Implementar una política de autenticación adaptativa basada en el riesgo continuo que combine la información de sesión, verificación facial (ArcFace/InsightFace), detección de ataques de presentación (PAD) y biometría conductual (Autoencoder) para autorizar o requerir verificación reforzada (*Step-Up*) en operaciones logísticas sensibles (`/api/logistics/*`).

## Alcance Backend
* **Auditoría de Componentes Biométricos:** Evaluación de ArcFace, PAD, Autoencoder conductual y puntuaciones de anomalía de sesión.
* **Modelo de Riesgo & Fusión Ponderada:** Normalización de puntajes dispares mediante adaptadores explícitos (`FaceRiskAdapter`, `PadRiskAdapter`, `BehaviorRiskAdapter`, `SessionRiskAdapter`) y motor de fusión `RiskFusionService`.
* **Desafíos Step-Up (`StepUpChallenge`):** Flujo de vida controlado (`PENDING`, `PASSED`, `FAILED`, `EXPIRED`, `LOCKED`) con TTL estricto y límite de intentos.
* **Prueba Sever-Side de Autorización Reforzada (`StepUpProof`):** Tokens opacos de un solo uso vinculados rígidamente a `(user_id, session_id, device_id, permission_code, action_code, resource_type, resource_id)`.
* **Separación Estricta de Datos:** Aislamiento total entre tablas biométricas y tablas del dominio logístico. Sin almacenamiento de imágenes ni embeddings en registros de auditoría ni entidades logísticas.
* **Auditoría Unificada de Seguridad:** Registro inmutable de eventos `logistics.security.*`.

## Estado
* **Estado General:** `IMPLEMENTADO` / `COMPROBADO`
* **Tests Unitarios e Integración:** 22/22 pasados en `tests/test_logistics_phase009.py`.
