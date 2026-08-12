# 04 — Estrategia de Base de Datos y Migraciones Controladas

## Ejecución de Migraciones Out-of-Band
Para evitar condiciones de carrera entre múltiples instancias de Cloud Run escaladas horizontalmente:
1. **NO ejecutar `alembic upgrade head` durante el inicio del contenedor en producción.**
2. Las migraciones se ejecutan mediante una tarea independiente (**Cloud Run Job** de migración) previa al despliegue del servicio web HTTP.

## Estrategia Expand-and-Contract
Para garantizar cero tiempo de inactividad durante las actualizaciones de esquema:
* **Fase EXPAND:** Añadir tablas o columnas opcionales que permitan la coexistencia de la versión anterior del código.
* **Fase MIGRATE:** Completar datos de forma asíncrona.
* **Fase CONTRACT:** Eliminar columnas/tablas obsoletas en una versión posterior.
