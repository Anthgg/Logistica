# Snapshot y documento CIT

El snapshot de la cita reúne aviso/revisión, OC, líneas, carga, transporte, horario y requisitos. Su hash permite demostrar qué datos generaron el documento.

```mermaid
flowchart LR
  APPT["Cita confirmada"] --> SNAP["Snapshot canónico"]
  SNAP --> PREVIEW["Preview PDF sin número"]
  SNAP --> ISSUE["Emisión con serie y secuencia"]
  ISSUE --> CIT["CIT ISSUED + artefacto autoritativo"]
```

Se reutiliza `DocumentLifecycleService`. Preview nunca asigna número, serie ni instancia emitida. La emisión es idempotente y el PDF autoritativo queda en almacenamiento documental.

