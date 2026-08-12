# 27. Reasignación

La reasignación ordinaria se solicita antes de iniciar descarga. Se genera un plan nuevo; al confirmar, la transacción valida el hash antes de marcar la asignación previa `SUPERSEDED`, cancela ocupación previa si existe y enlaza ambos registros.

No se permite una ventana donde el Gate Check-In quede con dos asignaciones activas confirmadas.

