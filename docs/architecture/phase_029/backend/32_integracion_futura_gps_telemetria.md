# Contrato de Integración Futura: GPS y Telemetría

## Propósito
Garantizar que los identificadores de conductor sean consumibles por dispositivos de telemetría e identificadores en cabina (iButton, RFID) sin exponer datos personales.

## Seguridad y Privacidad
- La telemetría solo utiliza el `driver_code` (`DRV-000001`) u objeto `DriverSummary`.
- Cero transmisión de DNI, números de licencia o teléfonos en payloads de telemetría en tiempo real.
