# Calendario de recepción

Cada almacén puede tener un calendario principal activo. El calendario define zona horaria IANA, anticipación mínima/máxima, duración de slot, capacidad por defecto, duración de holds y límites de reprogramación/cancelación.

```mermaid
flowchart TD
  WH["Warehouse"] --> CAL["ReceptionCalendar"]
  CAL --> WIN["OperatingWindow"]
  CAL --> BO["Blackout"]
  CAL --> HOLD["Hold"]
  CAL --> APPT["Appointment"]
```

Los estados son `DRAFT`, `ACTIVE`, `INACTIVE` y `ARCHIVED`.

