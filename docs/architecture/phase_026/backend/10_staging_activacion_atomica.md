# 10 — Flujo de Ingesta, Staging y Activación Atómica (Continuación Técnicamente Detallada)

## 1. Garantías ACID en la Conmutación de Puntero

La activación atómica de padrones asegura las siguientes propiedades ACID en el motor PostgreSQL:

1. **Atomicidad**: El cambio de puntero de la versión previa a la versión nueva ocurre en un solo bloque transaccional. Ningún usuario puede observar un estado donde existan dos versiones activas simultáneamente o ninguna versión activa.
2. **Consistencia**: Las restricciones de clave foránea `dataset_version_id` garantizan que todos los registros de contribuyentes estén completamente persistidos en `ruc_registry_entries` antes de ejecutar la conmutación.
3. **Aislamiento**: Se utiliza el nivel de aislamiento `READ COMMITTED` (o `REPEATABLE READ` durante la evaluación de anomalías) para evitar lecturas sucias durante la fase de staging.
4. **Durabilidad**: Una vez ejecutado el `COMMIT`, los cambios persisten en el WAL (Write-Ahead Log) de PostgreSQL.

---

## 2. Arquitectura de Inserción Masiva (`COPY` PostgreSQL)

Para lograr velocidades de ingesta superiores a 25,000 registros/segundo, la infraestructura utiliza la sentencia nativa `COPY ruc_registry_entries FROM STDIN` de PostgreSQL cuando se ejecuta en entornos de producción sobre motores asíncronos (`asyncpg`).
