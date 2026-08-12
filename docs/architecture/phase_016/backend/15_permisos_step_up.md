# 15 — Permisos y Step-Up

## Permiso Requerido en Fase 016
Todos los endpoints de inbound documents requieren:
```
logistics.documents.read
```
Este permiso se verifica mediante `require_permission("logistics.documents.read")` en el dependency injection de FastAPI.

## Autenticación Continua
Los endpoints heredan el sistema de autenticación continua del backend: cookies HTTP-only, validación de sesión activa y verificación de dispositivo.

## Datos Sensibles — Step-Up Pendiente
Los identificadores del conductor (DNI, licencia) se enmascaran automáticamente en Fase 016 para **todos los usuarios** con `logistics.documents.read`.

En fases futuras, para acceder a datos sin enmascarar, se requerirá:
- Permiso adicional: `logistics.documents.sensitive_read`
- Autenticación step-up (re-confirmación de contraseña o MFA)
- Registro de auditoría de acceso sensible

Esta arquitectura está preparada para implementarlo sin modificar los schemas actuales, ya que los campos `_raw` ya están separados de los `_masked` en el modelo Pydantic.
