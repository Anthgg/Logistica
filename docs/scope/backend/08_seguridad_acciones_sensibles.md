# 08. Seguridad y Acciones Sensibles — Proyecto T1

## 1. Integración con la Autenticación Existente

La API logística `/api/logistics` heredará y extenderá el middleware de seguridad del backend FastAPI:

1. **Sesiones y Cookies HTTP-Only:** Identificación mediante `access_token_cookie` firmado con la clave del sistema.
2. **Protección CSRF:** Header obligatorio `X-CSRF-Token` contra `csrf_access_token` en operaciones mutantes (`POST`, `PUT`, `PATCH`, `DELETE`).
3. **Autenticación Continua (`continuous_auth`):** Transmisión y evaluación periódica del score de riesgo derivado del comportamiento del usuario (teclado/mouse) y biometría pasiva.
4. **Step-Up Authentication (Re-autenticación Reforzada):** Interceptación de endpoints para acciones de alto riesgo cuando el score de riesgo supera el umbral permitido o la acción es de alto impacto operativo/financiero.

---

## 2. Catálogo de Acciones Sensibles

Las siguientes operaciones requerirán validación explícita de Step-Up (OTP SMS/Email o validación biométrica facial fresca) y registro de auditoría reforzado:

| Acción Sensible | Nivel de Riesgo | Rol Autorizado | Requisito Step-Up | Evidencia / Auditoría Obligatoria |
|---|---|---|---|---|
| Aprobar Orden de Compra > $5,000 | CRÍTICO | `ACT_GER`, `ACT_APROB` | Sí (Biométrico / OTP) | Justificación + Cuadro Comparativo |
| Anular Guía de Remisión / Documento Emitido | ALTO | `ACT_GER`, `ACT_ADM` | Sí (OTP) | Motivo legal y aprobación registrada |
| Ajuste Manual de Inventario (Entrada/Salida) | CRÍTICO | `ACT_GER`, `ACT_ADM` | Sí (Biométrico / OTP) | Acta de Toma de Inventario adjunta |
| Liberación Manual de Cuarentena (Rechazado) | ALTO | `ACT_CAL` (Supervisor) | Sí (OTP) | Reporte Técnico de Calidad Firmado |
| Cancelación de Despacho en Muelle | MEDIO | `ACT_DES` (Jefe) | Sí (OTP) | Registro de causa de cancelación |
| Re-asignación de Conductor/Vehículo en Ruta | MEDIO | `ACT_PLN` | No (Score Normal) | Log de cambio con motivo operativo |
| Cierre Forzado de Viaje | ALTO | `ACT_GER` | Sí (OTP) | Informe de cierre de emergencia |
| Confirmación Manual de Entrega sin POD | ALTO | `ACT_GER` | Sí (Biométrico) | Carta de conformidad física del cliente |
| Autorización de Devolución de Alto Valor | MEDIO | `ACT_REC` (Jefe) | Sí (OTP) | Fotos de inspección en almacén |
| Exportación Masiva de Clientes / Precios | ALTO | `ACT_ADM`, `ACT_GER` | Sí (Biométrico) | Log con hash de archivo descargado |

---

## 3. Protocolo de Auditoría Inmutable (`AuditEvent`)

Para cada acción sensible ejecutada en `/api/logistics`, el backend generará automáticamente un registro inmutable en la tabla `audit_events` que contendrá:

- `event_id`: UUID único.
- `user_id`: Identificador del usuario autenticado.
- `session_id`: ID de la sesión activa.
- `continuous_auth_score`: Score de confianza biométrica al momento exacto de la petición.
- `endpoint`: Ruta invocada (ej: `/api/logistics/inventory/adjustments`).
- `action`: Código de acción sensible (ej: `INVENTORY_MANUAL_ADJUSTMENT`).
- `ip_address`: IP de origen del cliente.
- `user_agent`: Cabecera User-Agent de la solicitud.
- `payload_hash`: Hash SHA-256 de los datos enviados.
- `timestamp`: Marca de tiempo ISO-8601 UTC.
