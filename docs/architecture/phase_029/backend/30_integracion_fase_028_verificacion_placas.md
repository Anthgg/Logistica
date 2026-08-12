# Contrato de Integración con Fase 028 (Verificación de Placas)

## Propósito
Especifica el desacoplamiento y compatibilidad entre el estado de verificación vehicular de Fase 028 y la elegibilidad del conductor de Fase 029.

## Reglas de Cruce
- Un conductor con estado `ELIGIBLE` puede ser asignado a un vehículo con estado de verificación `COMPLIANT`.
- Si el vehículo tiene fallas de verificación de placa (Fase 028), el despacho futuro rechazará la asignación combinada.
- Ambas evaluaciones operan mediante resolutores de dominio independientes.
