# Notificaciones y outbox

Los cambios de estado y recordatorios generan eventos en `arrival_notice_outbox_events` dentro de la misma transacción. La clave de deduplicación es única por tenant.

```mermaid
sequenceDiagram
  participant S as Servicio de dominio
  participant DB as PostgreSQL
  participant W as Job outbox
  participant A as Adaptador externo
  S->>DB: Cambio + evento PENDING
  W->>DB: SELECT FOR UPDATE SKIP LOCKED
  W->>A: Publicar
  A-->>W: OK o error
  W->>DB: PUBLISHED o FAILED con backoff
```

El adaptador externo es intercambiable. Sin adaptador configurado, el límite local permite pruebas deterministas sin afirmar que se envió correo/SMS.

