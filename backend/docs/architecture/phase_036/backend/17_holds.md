# Holds

Un hold reserva temporalmente capacidad para un aviso listo para programación. Sólo puede existir un hold activo por aviso; expira según el calendario y tiene un máximo de renovaciones.

```mermaid
sequenceDiagram
  participant C as Cliente
  participant API as Backend
  participant DB as PostgreSQL
  C->>API: Crear hold con Idempotency-Key
  API->>DB: Lock calendario y capacidad
  DB-->>API: Hold ACTIVE
  C->>API: Crear cita
  API->>DB: Consumir hold
  DB-->>API: Cita PROPOSED
  C->>API: Confirmar
  API->>DB: Revalidar y confirmar
```

El job de expiración cambia `ACTIVE` a `EXPIRED` y registra un evento de outbox.

