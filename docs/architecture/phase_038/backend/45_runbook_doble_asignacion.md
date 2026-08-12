# 45. Runbook: doble asignación

1. Detener confirmaciones para el almacén afectado.
2. Consultar asignaciones activas por Gate, vehículo y dock/slot.
3. Verificar índice parcial, logs de `DOCK_ASSIGNMENT_CONFLICT` y cadena de eventos.
4. No borrar filas. Solicitar cancelación/reasignación auditada.
5. Si el índice falta, restaurarlo mediante migración aprobada y ejecutar prueba concurrente.

