# Capacidad y disponibilidad

La disponibilidad resta citas y holds activos del máximo concurrente, pallets, bultos y peso del calendario/ventana. Los pesos se convierten con el motor de unidades.

Cada consulta devuelve hora del servidor y `availability_version` SHA-256. La respuesta es informativa: la confirmación vuelve a validar bajo lock para evitar sobrecupo por carrera.

El permiso crítico `logistics.reception_calendars.override_capacity` permite excepción explícita, con motivo, step-up y auditoría.

