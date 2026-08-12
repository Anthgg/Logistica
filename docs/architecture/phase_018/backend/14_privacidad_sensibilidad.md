# Privacidad de Datos Sensibles (Phase 018)

## Enmascaramiento del Conductor
DNI y licencias del conductor se enmascaran en el backend usando la función `mask_driver_id`:
- DNI `12345678` -> `******78`
- Licencia `Q49876521` -> `*******21`

## Gating de Datos de Clientes y Destino
```mermaid
graph TD
    Req[Solicitud Preview] --> PermCheck{¿Tiene permiso sensitive?}
    PermCheck -->|Sí| Reveal[Mostrar número telefónico completo]
    PermCheck -->|No| Mask[Enmascarar teléfono del cliente]
```
