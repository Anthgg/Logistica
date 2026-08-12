# 40. Auditoría

Los eventos usan el catálogo central y capturan usuario, roles, sesión, dispositivo, nivel de autenticación, riesgo, correlación, IP, user-agent, organización, almacén, recurso, motivo y cambios relevantes.

El maestro de muelles usa audit/outbox transaccional; el flujo operativo añade además la cadena append-only.

