# 28. Eventos operativos

`dock_operational_events` es append-only, secuenciado por Gate Check-In y encadenado con SHA-256. Cada evento incluye actor snapshot, correlación, payload resumido, hash anterior y hash actual. La escritura comparte transacción con outbox y estado.

