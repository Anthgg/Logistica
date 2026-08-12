# 04 — Catálogo de Documentos Externos

## Clasificación de Documentos Externos
Documentos emitidos por terceros (proveedores, transportistas, entidades regulatorias) catalogados como `EXTERNAL_RECEIVED` o `EXTERNAL_REFERENCED`.

| Tipo Documental Externo | Familia | Módulo Consumidor | Retención Requerida | Sensibilidad |
| :--- | :--- | :--- | :--- | :--- |
| **Guía de remisión del remitente** | `EXTERNAL_COMMERCIAL` | `receptions` | `RET_LEGAL_COMMERCIAL` | `CONFIDENTIAL` |
| **Guía del transportista** | `EXTERNAL_COMMERCIAL` | `receptions` | `RET_LEGAL_COMMERCIAL` | `CONFIDENTIAL` |
| **Factura de proveedor** | `EXTERNAL_COMMERCIAL` | `purchases` | `RET_LEGAL_COMMERCIAL` | `CONFIDENTIAL` |
| **SOAT** | `EXTERNAL_VEHICLE` | `gate_control` | `RET_EXTERNAL_LEGAL` | `RESTRICTED` |
| **Revisión técnica vehicular** | `EXTERNAL_VEHICLE` | `gate_control` | `RET_EXTERNAL_LEGAL` | `RESTRICTED` |
| **Licencia de conducir** | `EXTERNAL_DRIVER` | `gate_control` | `RET_EXTERNAL_LEGAL` | `CRITICAL` |
| **Certificado de calidad / MSDS** | `EXTERNAL_QUALITY` | `quality` | `RET_LEGAL_COMMERCIAL` | `INTERNAL` |
