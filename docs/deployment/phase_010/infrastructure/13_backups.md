# 13 — Política de Respaldos (Backups)

## Respaldos de Base de Datos
* **Frecuencia:** Copias de seguridad automáticas diarias.
* **Point-in-Time Recovery (PITR):** Retención de logs WAL para recuperación a un segundo específico hasta 7 días en el pasado.
* **Respaldo Pre-Despliegue:** Creación de un snapshot explícito antes de cualquier migración de producción.
* **Prueba de Restauración:** Verificación semestral de restauración de respaldo en base aislada de pruebas.
