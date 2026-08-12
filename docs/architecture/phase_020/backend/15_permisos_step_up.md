# 15. Permisos y Autenticación Step-Up

Las transacciones documentales de alta sensibilidad exigen una re-verificación de la identidad del operador (Step-Up).

## Matriz de Seguridad

| Acción | Permiso Requerido | Nivel de Riesgo | Challenge Requerido |
|---|---|---|---|
| Crear Borrador / Preview | `logistics.documents.preview` | LOW | Ninguno |
| Emitir Documento | `logistics.documents.issue` | HIGH | OTP / Biometría |
| Reimprimir Documento | `logistics.documents.reprint` | HIGH | OTP |
| Anular Documento | `logistics.documents.cancel` | CRITICAL | Step-Up CRITICAL |
| Descargar Original de Anulado | `logistics.audit.read_sensitive` | CRITICAL | Step-Up CRITICAL |
