# 12. Matriz de Inclusión y Exclusión — Proyecto T1

## Matriz Clasificada de Funcionalidades Backend

| ID | Funcionalidad | Estado de Alcance | MVP | Prioridad | Motivo / Criterio de Aceptación | Exclusión Temporal / Fase Futura |
|---|---|---|---|---|---|---|
| F01 | CRUD de Maestros Logísticos | INCLUIDA | MVP 1 | ALTA | Necesario para catalogar SKUs, ubicaciones y entidades. | Ninguna. |
| F02 | Consulta RUC a SUNAT | INCLUIDA | MVP 1 | ALTA | Validación automática de proveedores/clientes por API/padrón. | Ninguna. |
| F03 | Verificación Vehicular y Brevetes | INCLUIDA | MVP 1 | MEDIA | Confirmación de validez de flota/conductores antes de asignación. | Ninguna. |
| F04 | Motor de Documentos PDF y Storage | INCLUIDA | MVP 1 | ALTA | Generación asíncrona de Guías/Actas guardadas en Cloud Storage. | Ninguna. |
| F05 | Requerimientos y Cotizaciones | INCLUIDA | MVP 2 | MEDIA | Control del proceso de abastecimiento pre-orden de compra. | Ninguna. |
| F06 | Órdenes de Compra y Aprobaciones | INCLUIDA | MVP 2 | ALTA | Emisión de O/C con regla de Step-Up si supera el umbral. | Ninguna. |
| F07 | Recepción en Garita y Muelle | INCLUIDA | MVP 2 | ALTA | Control de acceso vehicular y actas de descarga. | Ninguna. |
| F08 | Inspección de Calidad / Cuarentena | INCLUIDA | MVP 2 | MEDIA | Mapeo de lotes a estado de cuarentena y liberación formal. | Ninguna. |
| F09 | Kardex e Inventario en Tiempo Real | INCLUIDA | MVP 2 | CRÍTICA | Cálculo transaccional de stock por SKU/Ubicación/Lote/Serie. | Ninguna. |
| F10 | Reservas Atómicas de Stock | INCLUIDA | MVP 2 | CRÍTICA | Prevención de sobreventa o reservas duplicadas en base de datos. | Ninguna. |
| F11 | Picking y Packing (LPN) | INCLUIDA | MVP 2 | ALTA | Recolección y empaquetado etiquetado en almacén. | Ninguna. |
| F12 | Despacho y Guías de Remisión | INCLUIDA | MVP 2 | ALTA | Salida física de almacén y emisión de documento de transporte. | Ninguna. |
| F13 | Programación de Viajes y Rutado | INCLUIDA | MVP 3 | MEDIA | Consolidación de carga y paradas mediante motor OSRM/Valhalla. | Ninguna. |
| F14 | Telemetría GPS en Vivo | INCLUIDA | MVP 3 | MEDIA | Ingesta de coordenadas GPS desde App Móvil de conductor. | Ninguna. |
| F15 | Prueba de Entrega Digital (POD) | INCLUIDA | MVP 3 | ALTA | Captura de firma, foto de evidencia y validación OTP. | Ninguna. |
| F16 | Devoluciones (RMA) e Incidencias | INCLUIDA | MVP 3 | MEDIA | Registro y re-ingreso de mercadería no entregada. | Ninguna. |
| F17 | Notificaciones SMS/Email/Push | INCLUIDA | MVP 3 | BAJA | Alertas automáticas de desvíos y entregas. | Ninguna. |
| F18 | Cálculo de KPIs (OTIF, ERI) | INCLUIDA | Consolidación | MEDIA | Indicadores de desempeño para tablero gerencial. | Ninguna. |
| F19 | Facturación Electrónica Automática | EXCLUIDA | N/A | N/A | Complejidad regulatoria PSE/OSE SUNAT. | Fase 005 (Integración Tributaria). |
| F20 | Emisión Comprobantes de Pago SUNAT | EXCLUIDA | N/A | N/A | El MVP es 100% operativo y de control logístico. | Fase 005. |
| F21 | Contabilidad y Planillas / Nómina | EXCLUIDA | N/A | N/A | Fuera del alcance del sistema T1. | Excluido permanentemente. |
| F22 | Marketplace / E-commerce B2C | EXCLUIDA | N/A | N/A | Enfoque exclusivo en logística B2B de AndesLog. | Excluido permanentemente. |
| F23 | Predicción Demanda con IA | EXCLUIDA | N/A | N/A | Requiere histórico de datos no disponible en MVP. | Fase 006 (Analítica Avanzada). |
| F24 | Scraping no Autorizado / CAPTCHA | EXCLUIDA | N/A | N/A | Riesgo de inestabilidad y bloqueo legal. | Excluido permanentemente. |
