# 08 — Integración con Endpoints Sensibles y Flujo de Intercepción

## Intercepción y Respuesta HTTP 428 / 403

Cuando un cliente intenta realizar una operación protegida por un permiso sensible (ej: `POST /api/logistics/role-assignments`):
1. El backend valida autenticación (Cookie HTTP-only), CSRF, RBAC y alcance.
2. `StepUpService` evalúa si el permiso requiere verificación reforzada. Si requiere step-up y no se incluye la cabecera `X-Step-Up-Proof` (o la prueba es inválida/expirada), el backend responde con error estructurado:
   ```json
   {
     "error": {
       "code": "STEP_UP_REQUIRED",
       "message": "Esta acción requiere verificación adicional.",
       "challenge_id": "8f3b2a1c-...",
       "required_factors": ["face", "pad"],
       "expires_at": "2026-07-26T21:15:00Z",
       "attempts_remaining": 3
     }
   }
   ```
3. El cliente completa el desafío y obtiene el `proof_token`.
4. El cliente reenvía la petición original incluyendo `X-Step-Up-Proof: proof_token`.
5. El backend consume atómicamente la prueba (`StepUpService.consume_proof()`) y ejecuta la acción sensible.
