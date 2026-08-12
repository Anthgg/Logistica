# Modelo ReceptionAppointment

La cita enlaza tenant, sede, almacén, calendario, aviso y revisión congelada. Conserva slot, zona horaria, carga esperada, snapshots de proveedor/transportista/vehículo/conductor y punteros documentales.

La unicidad del código se aplica por organización. `row_version` soporta control optimista y los locks de confirmación/reprogramación soportan concurrencia pesimista.

Estados principales: `PROPOSED`, `PENDING_CONFIRMATION`, `CONFIRMED`, `RESCHEDULE_REQUESTED`, `RESCHEDULED` y `CANCELLED`.

