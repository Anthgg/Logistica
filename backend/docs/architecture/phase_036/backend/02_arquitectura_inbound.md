# Arquitectura inbound

La arquitectura sigue `domain / application / infrastructure / presentation`. Los servicios de aplicación coordinan invariantes, locks, snapshots, auditoría e idempotencia; FastAPI sólo adapta contratos HTTP.

```mermaid
flowchart LR
  OC["OC emitida y revisión congelada"] --> AN["ArrivalNotice DRAFT"]
  AN --> REV["Revisión editable"]
  REV --> SUB["SUBMITTED e inmutable"]
  SUB --> APP["Cita de recepción"]
```

Los módulos reutilizados se referencian por UUID y snapshot; no se duplican catálogos.

