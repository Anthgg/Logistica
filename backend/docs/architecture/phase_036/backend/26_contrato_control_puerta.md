# Contrato para control de puerta

`GET /reception-appointments/{id}/gate-preparation` entrega información de preparación, no ejecuta check-in.

```mermaid
flowchart TD
  CIT["Cita/CIT"] --> PREP["Gate preparation"]
  PREP --> SLOT["Ventana esperada"]
  PREP --> PLATE["Placa esperada"]
  PREP --> DRIVER["Conductor esperado"]
  PREP --> GUIDES["Guías y documentos"]
  PREP --> WARN["Advertencias"]
  PREP -.-> FUTURE["Capacidades de check-in: vacías"]
```

La Fase 037 podrá consumir este contrato, pero deberá crear sus propias entidades y permisos físicos.

