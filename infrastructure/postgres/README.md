# PostgreSQL

Los datos viven en el volumen nombrado `postgres_data`. El puerto de desarrollo
se publica solo en `127.0.0.1`; la superposición de producción elimina esa
publicación y PostgreSQL queda accesible únicamente por `app_network`.

Antes de una actualización o migración importante se debe crear y comprobar un
respaldo con `pg_dump`. No ejecute `docker compose down -v` salvo que quiera
eliminar de forma irreversible la base local.
