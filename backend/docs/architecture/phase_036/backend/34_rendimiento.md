# Rendimiento

Índices cubren tenant, almacén, proveedor/transportista, estado, fechas, OC/línea/producto, placa/conductor, slots, holds, outbox y package jobs.

Disponibilidad limita el rango solicitado y calcula un `availability_version`. Los workers procesan lotes ordenados con `SKIP LOCKED`. Los paquetes se generan fuera de la petición HTTP.

La prueba de calendario mide la generación de slots y exige menos de dos segundos en el escenario de regresión. Esto es un smoke test, no reemplaza una prueba de carga con datos de producción anonimizados.

