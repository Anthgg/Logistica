# 29. Tiempos autoritativos

Movimiento, llegada, inicio, pausa, reanudación, finalización, aborto y liberación usan reloj UTC del servidor. Pydantic usa `extra="forbid"`, de modo que campos como `started_at`, `completed_by`, `status` o duraciones son rechazados.

