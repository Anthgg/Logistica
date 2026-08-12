# Migración

La revisión `y360110036dc` depende de `x350110035dc`. Crea 16 tablas de Fase 036, PK/FK, checks, índices, constraints únicas y tres FK diferidas para punteros circulares.

La migración siembra permisos y asignaciones a roles existentes. El downgrade elimina primero FK circulares, luego tablas en orden inverso y finalmente permisos de la fase.

Se verificó en PostgreSQL aislado con `upgrade`, `downgrade` a Fase 035 y nuevo `upgrade`. No se ejecutó contra producción.

