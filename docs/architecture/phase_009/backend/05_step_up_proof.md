# 05 — StepUpProof y Prueba de Autorización Reforzada

## Estructura y Vínculo de Seguridad
Un `StepUpProof` es una prueba server-side de autorización que se genera únicamente cuando un `StepUpChallenge` alcanza el estado `PASSED`.

Campos clave de vinculación:
* `user_id`: ID del usuario autenticado.
* `session_id`: ID de la sesión HTTP-only activa.
* `device_id`: ID del dispositivo registrado.
* `permission_code`: Permiso específico verificado (ej: `logistics.documents.cancel`).
* `action_code`: Código de acción.
* `resource_type` & `resource_id`: Recurso exacto protegido.
* `proof_hash`: Hash criptográfico SHA-256 generado en el servidor.
* `status`: `ACTIVE`, `CONSUMED`, `EXPIRED`, `REVOKED`.

## Reglas de Uso
1. **Single-Use:** La prueba se transiciona de `ACTIVE` a `CONSUMED` en el instante exacto en que la acción sensible es ejecutada. No se puede reutilizar para peticiones posteriores.
2. **TTL:** Validez máxima de 60 segundos (`PROOF_TTL_SECONDS`).
3. **Impredecible e Incorrompible:** El identificador devuelto al cliente es un UUID v4 opaco. El cliente NO puede construir ni falsificar este objeto.
