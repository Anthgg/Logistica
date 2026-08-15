# Contratos Protegidos y Políticas de Seguridad · Fase 001

## 1. Contrato de Seguridad de Cookies y Sesión

Todas las cookies de autenticación cumplen con las siguientes directivas de seguridad:

| Nombre Cookie | Flag HttpOnly | Flag Secure | Directiva SameSite | TTL / Max-Age | Propósito |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `session_token` | `True` | Dinámico (`secure` en prod) | `Lax` | 15 minutos (900 s) | Token JWT de acceso para llamadas a la API |
| `refresh_token` | `True` | Dinámico (`secure` en prod) | `Lax` | 30 días (con remember_me) / 8 horas | Token JWT para rotación y renovación de sesión |
| `device_token` | `True` | Dinámico (`secure` en prod) | `Lax` | 365 días | Identificación criptográfica de dispositivo conocido |
| `csrf_token` | `False` | Dinámico (`secure` en prod) | `Lax` | 1 hora (3600 s) | Doble envío CSRF, legible por cliente Frontend |

---

## 2. Contrato Anti-CSRF

1. **Métodos Protegidos:** `POST`, `PUT`, `PATCH`, `DELETE` requieren validación obligatoria de token CSRF.
2. **Métodos Exentos:** `GET`, `HEAD`, `OPTIONS` no modifican estado y están exentos.
3. **Mecanismo:** El cliente debe enviar el header `X-CSRF-Token` coincidiendo con la cookie `csrf_token` (validación en tiempo constante `secrets.compare_digest`).
4. **Respuesta en Violación:** Código HTTP `403 Forbidden` con error canónico `CSRF_VALIDATION_FAILED`.

---

## 3. Contrato de Rutas Frontend (Anti-Double-Prefix)

El cliente API del frontend (`api-client.ts`) implementa una validación estricta de rutas:
- La función `buildUrl(path: string)` valida que la ruta relativa **no comience con `/api/`** o `api/`.
- Si se detecta un prefijo indebido, lanza inmediatamente `ApplicationError("INVALID_API_PATH")`.
- Esto previene defectos de doble prefijo tipo `/api/api/logistics/...`.
- `credentials: 'include'` es obligatorio en todas las peticiones `fetch`.

---

## 4. Estructura Canónica de Errores

Todas las respuestas de error en el backend retornan un payload JSON estandarizado:

```typescript
interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    request_id: string;
    timestamp: string;
    details: Record<string, unknown> | null;
  };
}
```

Códigos de error estándar verificados en Fase 001:
- `INVALID_CREDENTIALS` (401)
- `SESSION_REQUIRED` (401)
- `SESSION_EXPIRED` (401)
- `SESSION_REVOKED` (401)
- `REFRESH_TOKEN_REQUIRED` (401)
- `REFRESH_TOKEN_EXPIRED` (401)
- `REFRESH_TOKEN_REUSED` (401)
- `ACCOUNT_DISABLED` (403)
- `ACCOUNT_TEMPORARILY_LOCKED` (423)
- `DEVICE_BLOCKED` (403)
- `CSRF_VALIDATION_FAILED` (403)
- `RESOURCE_NOT_FOUND` (404)
- `METHOD_NOT_ALLOWED` (405)
- `VALIDATION_ERROR` (422)
- `INTERNAL_SERVER_ERROR` (500)
