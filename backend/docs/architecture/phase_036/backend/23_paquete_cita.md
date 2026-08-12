# Paquete de cita

El paquete se solicita de forma asíncrona e idempotente. El job exige CIT emitida, obtiene el PDF autoritativo y produce un ZIP con `manifest.json` y referencias de documentos de transporte.

El artefacto `PACKAGE_ZIP` es sensible, no autoritativo y conserva SHA-256, tamaño, storage key y actor solicitante. La descarga expone el hash para verificación.

