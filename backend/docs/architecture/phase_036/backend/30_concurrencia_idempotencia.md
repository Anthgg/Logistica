# Concurrencia e idempotencia

Las operaciones sensibles bloquean OC/líneas, calendarios, holds, avisos y citas mediante `SELECT ... FOR UPDATE`; los workers usan `SKIP LOCKED`. La confirmación recalcula capacidad dentro de la transacción.

Las claves de idempotencia se guardan con hash del payload y respuesta. Misma clave más mismo payload devuelve el recurso anterior. Misma clave más payload distinto devuelve `409 IDEMPOTENCY_CONFLICT`.

Avisos, líneas, submit, holds, creación/confirmación/reprogramación/cancelación de cita, emisión CIT y paquetes tienen contratos idempotentes.

