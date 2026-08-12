# 34. Documentos y exportaciones

La tabla `dock_operation_export_jobs` permite solicitudes persistentes e idempotentes. No se emite documento oficial porque no existe catálogo documental aprobado para Fase 038: `PENDIENTE_CATÁLOGO_DOCUMENTAL`.

La exportación sensible exige permiso y step-up. El backend genera mediante job CSV protegido contra CSV injection, XLSX y PDF con la etiqueta `REPORTE OPERATIVO - NO OFICIAL`; crea un `FileAsset` privado, registra solicitud, resultado y descarga. La emisión oficial sigue bloqueada hasta aprobar tipo documental, versión, retención y plantilla.
