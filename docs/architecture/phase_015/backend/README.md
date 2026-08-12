# Fase 015 — Diseñar Documentos de Compras (REQ, SCOT, CCO, OC, APC, CEP) (Backend)

## Resumen Ejecutivo
La Fase 015 implementa las plantillas documentales especializadas de la familia **PURCHASING** para **Proyecto T1**, cubriendo los 6 documentos obligatorios del proceso de abastecimiento:
1. **REQ:** Requerimiento de Compra (`purchasing.req` v1.0.0)
2. **SCOT:** Solicitud de Cotización (`purchasing.scot` v1.0.0)
3. **CCO:** Cuadro Comparativo de Ofertas (`purchasing.cco` v1.0.0)
4. **OC:** Orden de Compra (`purchasing.oc` v1.0.0)
5. **APC:** Aprobación de Compra (`purchasing.apc` v1.0.0)
6. **CEP:** Constancia de Envío al Proveedor (`purchasing.cep` v1.0.0)

## Alcance
- **Plantillas HTML & Estilos CSS:** Herencia de la plantilla base `base.document` v1.0.0 y extensión visual sobria `purchasing.css`.
- **Esquemas y Validación:** Validadores Pydantic v2 con precisión `Decimal` para cálculos financieros y montos.
- **Modo Preview Protegido:** Marca de agua `VISTA PREVIA` sin consumo ni reserva de secuencias correlativas.
- **Endpoints REST Protegidos:** `/api/logistics/purchasing/documents/{doc_type}/preview` y `/pdf`.
- **Migración y Registro:** `f550860015dc_add_purchasing_document_templates.py` integrando los tipos `APC` y `CEP`.
- **Pruebas:** Cobertura de las 6 plantillas de compras en `tests/test_logistics_phase015.py`.
