# 17. Especificación de Endpoints

Endpoints FastAPI expuestos en la Fase 020 bajo el prefijo `/api/logistics`:

- `GET /documents`: Filtrado paginado e indexado de documentos.
- `POST /documents`: Crear borrador.
- `PUT /documents/{id}`: Actualizar borrador.
- `GET /documents/{id}`: Obtener detalle técnico.
- `GET /documents/{id}/history`: Obtener línea de tiempo del ciclo de vida.
- `GET /documents/{id}/preview`: Visualizar previsualización PDF (inline).
- `GET /documents/{id}/pdf`: Descargar archivo PDF oficial adjunto.
- `POST /documents/{id}/issue`: Confirmar emisión.
- `POST /documents/{id}/print-events`: Registrar intención de impresión.
- `POST /documents/{id}/reprint`: Solicitar reimpresión oficial.
- `POST /documents/{id}/cancel`: Anular documento.
- `POST /documents/export`: Generar trabajo asíncrono de exportación ZIP.
- `GET /documents/exports/{job_id}`: Consultar estado de exportación.
- `GET /documents/exports/{job_id}/download`: Descargar ZIP listo.
- `GET /document-series/{series_id}/talonario.pdf`: PDF del talonario.
- `GET /document-talonarios/{talonario_id}/pdf`: PDF de talonario por ID.
- `POST /document-talonarios/{talonario_id}/exports`: Exportar talonario a ZIP.
- `GET /document-packages/{operation_type}/{operation_id}.zip`: ZIP por operación.
