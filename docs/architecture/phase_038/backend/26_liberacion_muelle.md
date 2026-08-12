# 26. Liberación de muelle

Solo una operación `COMPLETED` o `ABORTED` puede liberar. Se cierra la ocupación, la asignación pasa a `DOCK_RELEASED`, se fija actor/hora y se emiten evento, outbox y auditoría. Una descarga abortada requiere motivo.

