# 19 — Integración Futura: Ingreso

## Módulo de Scheduling (Citas) — Fase 041+
- API REST para crear, modificar y cancelar citas de recepción reales
- Gestión de ventanas horarias por muelle y almacén
- Confirmación bidireccional con proveedores (email/webhook)
- El CIT actual pasará de documento de preview a documento oficial con correlativo reservado

## Control de Puerta Físico — Fase 042+
- Integración con sensores RFID para lectura automática de placa
- Barreras automatizadas controladas por la decisión del CPV
- Captura fotográfica del vehículo vinculada al CPV
- Registro de salidas vehiculares post-descarga (el CPV actual solo registra ingresos)

## Guías de Remisión Electrónicas — Fase futura SUNAT
- Integración con la API de SUNAT para validar guías de remisión electrónicas (GRE)
- Cruce automático del número de guía del transportista con los registros fiscales
- El campo `waybill_reference` del AREC se vinculará al registro fiscal

## Fotografías y Evidencias
- Captura y almacenamiento de fotos del vehículo, precintos y descarga
- Vinculación de evidencias fotográficas al CPV y al DIF
- El componente `evidence_references.html` está preparado para esto
