# Contrato de Integración Futura: Despacho y Viajes

## Propósito
Define el contrato que consumirán los módulos de Despacho (Fase 048+), Planificación de Transporte y Viajes para asignar conductores operativamente.

## Puntos de Extensión
1. Endpoint `POST /api/logistics/drivers/{driver_id}/vehicle-compatibility`
2. Endpoint `GET /api/logistics/drivers/{driver_id}` (verificación de `eligibility_status == 'ELIGIBLE'`).
3. Bloqueo automático de despacho si la elegibilidad es `INELIGIBLE`, `LICENSE_EXPIRED` o `BLOCKED`.
