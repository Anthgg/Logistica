# 19. Responsables

Se validan usuarios activos y contratistas activos. No se acepta una referencia de equipo porque no existe catálogo aprobado; se devuelve un error estable en lugar de inventarlo.

```mermaid
flowchart LR
  U["Usuario"] --> V["Validación"]
  P["Partner"] --> V
  T["Team sin catálogo"] --> X["Rechazo"]
  V --> S["Snapshot autoritativo"]
```

Inicio requiere `DOCK_SUPERVISOR` y `UNLOADING_LEAD` activos.

