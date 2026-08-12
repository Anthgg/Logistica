# Integración futura con Fase 037

Fase 037 podrá leer la cita confirmada, CIT y `gate-preparation`. No debe inferir check-in a partir de `window_elapsed_at`.

```mermaid
flowchart LR
  P36["Fase 036: cita confirmada"] --> CONTRACT["Gate preparation read-only"]
  CONTRACT --> P37["Fase 037: control de puerta"]
  P37 --> CHECKIN["Check-in físico futuro"]
  P37 --> DOCK["Asignación de muelle futura"]
  P36 -. "no crea" .-> CHECKIN
  P36 -. "no crea" .-> DOCK
```

Los permisos y entidades físicas deberán pertenecer a Fase 037.

