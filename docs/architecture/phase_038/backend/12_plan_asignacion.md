# 12. Plan de asignación

El plan persiste muelles elegibles, incompatibilidades, warnings, intervalo, capacidades, prioridad, hash y expiración.

```mermaid
sequenceDiagram
  Client->>API: crear plan
  API->>DB: snapshot + hash + TTL
  API-->>Client: opciones y assignment_hash
  Client->>API: confirmar hash
  API->>DB: lock + revalidación
```

Un plan vencido o cuyo estado cambió se rechaza con conflicto.

