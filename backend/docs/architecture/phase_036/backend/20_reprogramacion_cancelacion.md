# Reprogramación

La reprogramación requiere una cita confirmada, respetar el cutoff y consumir un hold válido del mismo aviso. Se crea una cita reemplazo y la anterior queda `RESCHEDULED`; nunca se reescribe el slot histórico.

```mermaid
stateDiagram-v2
  CONFIRMED --> RESCHEDULE_REQUESTED
  RESCHEDULE_REQUESTED --> RESCHEDULED: consume hold
  RESCHEDULED --> [*]
  note right of RESCHEDULED
    Se crea otra cita PROPOSED
    con vínculo rescheduled_from
  end note
```

Solicitud y ejecución son idempotentes y quedan en historial, auditoría y outbox.

La cancelación exige motivo, permiso con step-up e idempotencia. Si la cita era la activa del aviso, éste vuelve a `READY_FOR_SCHEDULING`.

```mermaid
flowchart LR
  APPT["Cita activa"] --> CHECK["Validar cutoff"]
  CHECK -->|permitido| CANCEL["CANCELLED"]
  CANCEL --> READY["Aviso READY_FOR_SCHEDULING"]
  APPT --> ELAPSED["slot_end transcurrido"]
  ELAPSED --> FLAG["window_elapsed_at"]
  FLAG --> SAME["Estado no cambia; no no-show automático"]
```

El job de ventana transcurrida no declara `NO_SHOW`, porque eso requiere evidencia de una fase física posterior.
