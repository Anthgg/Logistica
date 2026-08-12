# Modelo ArrivalNotice

`arrival_notices` contiene identidad, alcance organizacional, almacén, proveedor, transportista opcional, fecha esperada y resúmenes de carga. El detalle mutable vive en una revisión.

```mermaid
flowchart TD
  AN["ArrivalNotice"] --> REV["ArrivalNoticeRevision"]
  REV --> POR["Referencias de OC"]
  POR --> LINE["Líneas esperadas"]
  LINE --> ALLOC["Allocations de cantidad"]
```

Los punteros `active_revision_id` y `confirmed_revision_id` usan FK diferidas para resolver el ciclo de creación sin perder integridad.

