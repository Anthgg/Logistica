# Fase 016 — Diseñar Documentos de Ingreso (CIT, CPV, AREC, NI, DIF, NC) (Backend)

## Resumen Ejecutivo
La Fase 016 implementa las plantillas documentales especializadas del paquete de recepción de mercadería para la familia **INBOUND** y **QUALITY** en **Proyecto T1**:
1. **CIT:** Cita de Recepción (`inbound.cit` v1.0.0, Familia INBOUND)
2. **CPV:** Control de Puerta Vehicular (`inbound.cpv` v1.0.0, Familia INBOUND)
3. **AREC:** Acta de Recepción (`inbound.arec` v1.0.0, Familia INBOUND)
4. **NI:** Nota de Ingreso (`inbound.ni` v1.0.0, Familia INBOUND)
5. **DIF:** Acta de Diferencias (`inbound.dif` v1.0.0, Familia INBOUND)
6. **NC:** No Conformidad (`quality.nc` v1.0.0, Familia QUALITY)

## Alcance
- **Plantillas HTML & Estilos CSS:** Herencia de la plantilla base `base.document` v1.0.0 y extensión visual `inbound.css`.
- **Privacidad y Enmascaramiento:** Enmascaramiento automático de identificadores sensibles (DNI `******42`, Licencia `Q4*****21`).
- **Paquete Documental:** Manifiesto de inclusión documental de recepción (`ReceptionDocumentPackageManifest`) basado en reglas.
- **Esquemas y Validación:** Validadores Pydantic v2 con precisión `Decimal` para cantidades y tiempos.
- **Modo Preview Protegido:** Marca de agua `VISTA PREVIA` sin consumo de correlativos ni creación de stock.
- **Endpoints REST Protegidos:** `/api/logistics/inbound/documents/{doc_type}/preview`, `/pdf` y `/document-package/manifest`.
- **Migración y Registro:** `g660970016dc_add_inbound_document_templates.py`.
- **Pruebas:** Cobertura de las 6 plantillas de ingreso/calidad en `tests/test_logistics_phase016.py`.
