# ODS — Orden de Salida (Phase 018)

## Propósito
La Orden de Salida (ODS) es la autorización formal emitida por el planificador para retirar mercancía del almacén.

## Límite de Liberación y Step-Up
Su previsualización muestra si requiere Step-Up (`step_up_status = PENDING_STEP_UP`), pero no realiza la liberación transaccional de stock:
- **Fase 056**: Emisión productiva de ODS.
- **Fase 057**: Step-up de liberación física mediante biometría / clave de seguridad.

## Mapeo del Step-Up en Preview
Mapea de forma no intrusiva el estado de autenticación reforzada del operador a través del campo `step_up_status`.
