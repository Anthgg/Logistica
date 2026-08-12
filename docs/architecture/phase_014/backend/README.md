# Fase 014 — Motor Central de Plantillas Documentales y Renderizado (Backend)

## Resumen Ejecutivo
La Fase 014 implementa el motor central de plantillas documentales para **Proyecto T1**, proporcionando una arquitectura unificada y tipada para la transformación de datos logísticos estructurados en vistas HTML validadas, archivos binarios PDF, metadatos de ejecución y códigos QR de verificación digital.

## Alcance
- **Renderizador Documental (`DocumentRenderer`):** Interfaz desacoplada y comandos tipados (`DocumentRenderCommand`, `HtmlRenderResult`, `PdfRenderResult`).
- **Plantilla Base Genérica (`base.document` v1.0.0):** Herencia mediante Jinja2 HTML y hoja de estilos de impresión `shared/print.css`.
- **Modo Preview Seguro:** Marca de agua visible (`VISTA PREVIA`), sin reservas de correlativos ni registros de emisión.
- **Generador de QR (`DocumentQRGenerator`):** Codificación Base64 PNG/SVG para verificación.
- **Base de Datos y Modelos:** `DocumentTemplateModel`, `DocumentTemplateVersionModel`, `DocumentTemplateAssetModel`.
- **Migración Alembic:** `e440750014dc_add_document_template_tables.py`.
- **Endpoints REST:** `/api/logistics/document-templates` y `/api/logistics/document-renderer/status`.
- **Pruebas:** 6 unitarias e integrales en `tests/test_logistics_phase014.py`.
