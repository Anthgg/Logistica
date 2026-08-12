# Conductor y licencia

El conductor puede provenir del maestro existente o ser una declaración excepcional autorizada. Se capturan nombre, identificadores redactados, categoría y vencimiento declarado.

```mermaid
flowchart LR
  DRIVER["Conductor maestro o declarado"] --> SNAP["Snapshot redactado"]
  SNAP --> LIC["Licencia y vencimiento declarado"]
  LIC --> JOB["Job de próximo vencimiento"]
  SNAP --> OVER["Detección de solapamiento por driver_id"]
```

El job no equivale a validación ante una autoridad externa; sólo evalúa el snapshot capturado.

