# 14. Solapamientos y concurrencia

La ejecución bloquea plan, cola, muelle y asignaciones activas. Índices parciales protegen Gate Check-In, vehículo, dock/slot, ocupación, operación y pausa.

```mermaid
sequenceDiagram
  participant T1
  participant DB
  participant T2
  T1->>DB: SELECT dock FOR UPDATE
  T2->>DB: espera lock
  T1->>DB: inserta asignación + commit
  T2->>DB: revalida y rechaza conflicto
```

La defensa principal funciona sin extensiones. Una exclusión GiST de rangos queda pendiente de aprobación DBA.

