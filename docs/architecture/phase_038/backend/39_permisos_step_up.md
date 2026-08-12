# 39. Permisos y step-up

Se agregaron 31 permisos. Lecturas son low/medium; asignar, reasignar, cancelar, iniciar, completar, abrir precinto y exportar son high; bloquear, blackouts, abortar, aprobar overrides y corregir tiempos son critical cuando corresponde.

Cada permiso marcado `requires_step_up` tiene una entrada fail-closed en el catálogo central. No se autoriza por nombre de rol dentro del dominio.

