# 10 — Catálogo de Eventos de Auditoría de Seguridad

## Eventos Registrados (`logistics.security.*`)

* `logistics.security.risk_evaluated`: Evaluación de riesgo de autenticación adaptativa realizada.
* `logistics.security.step_up_required`: Petición bloqueada temporalmente solicitando verificación reforzada.
* `logistics.security.challenge_created`: Desafío Step-Up emitido.
* `logistics.security.challenge_factor_submitted`: Envío de factor biométrico recibido.
* `logistics.security.challenge_passed`: Desafío Step-Up completado exitosamente.
* `logistics.security.challenge_failed`: Desafío Step-Up fallido por discrepancia biométrica.
* `logistics.security.challenge_locked`: Desafío bloqueado por exceso de intentos.
* `logistics.security.proof_issued`: Prueba `StepUpProof` de un solo uso emitida.
* `logistics.security.proof_consumed`: Prueba consumida en acción logística sensible.
* `logistics.security.pad_attack_detected`: Ataque de presentación (foto/pantalla) detectado por el PAD.
