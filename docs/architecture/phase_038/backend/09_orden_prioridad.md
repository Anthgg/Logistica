# 09. Orden y prioridad

El orden es determinista: peso de prioridad, instante listo/encolado y UUID como desempate. Cambiar prioridad exige versión optimista y motivo.

```mermaid
flowchart LR
  P["Prioridad"] --> S["Sort estable"]
  T["Tiempo servidor"] --> S
  I["UUID desempate"] --> S
```

Los niveles urgentes requieren justificación desde el contrato Pydantic.

