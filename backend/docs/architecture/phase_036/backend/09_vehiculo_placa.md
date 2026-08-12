# Vehículo y placa

El aviso puede referenciar un vehículo maestro o declarar datos excepcionales. Se guarda placa normalizada y snapshot; no se crea un maestro nuevo de forma implícita.

```mermaid
flowchart LR
  DECL["Vehículo o placa declarada"] --> SNAP["Snapshot en revisión"]
  SNAP --> VER["Resumen de verificación existente"]
  VER --> APPT["Snapshot en cita"]
  APPT --> OVER["Detección de solapamiento de placa"]
```

La verificación representa información existente o declarada; el backend no afirma una consulta externa inexistente.

