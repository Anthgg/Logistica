# 12 — Protección contra Repetición, Ataques y Concurrencia

## Vectores de Ataque Mitigados

1. **Reutilización de Proof (`Replay Attack`):** El estado del `StepUpProof` se actualiza de forma atómica a `CONSUMED` dentro de la transacción de la acción sensible. Peticiones concurrentes o posteriores con el mismo token fallan inmediatamente.
2. **Robo / Reasignación de Proof:** Cada `StepUpProof` valida que la `session_id`, `user_id`, `device_id`, `permission_code` y `resource_id` de la petición coincidan exactamente con los valores registrados al emitir la prueba.
3. **Inyección de Parámetros Frontend:** La API ignora cualquier cabecera o propiedad `risk_score`, `face_verified` o `step_up_passed` proveniente del cliente.
