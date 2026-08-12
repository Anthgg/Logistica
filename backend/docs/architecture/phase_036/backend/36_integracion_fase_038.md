# Integración futura con Fase 038

Fase 038 podrá partir de una llegada validada por Fase 037 y contrastarla con las líneas esperadas congeladas.

```mermaid
flowchart LR
  P36["Expected lines + allocations"] --> EXPECTED["Contrato esperado"]
  P37["Llegada/check-in futuro"] --> P38["Fase 038"]
  EXPECTED --> P38
  P38 --> UNLOAD["Descarga futura"]
  P38 --> RECEIVE["Recepción física futura"]
  P36 -. "no ejecuta" .-> UNLOAD
  P36 -. "no ejecuta" .-> RECEIVE
```

Esta fase no crea diferencias recibidas ni modifica allocations con cantidades físicas.

