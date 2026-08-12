# Arquitectura de Plantillas de Salida (Phase 018)

## Herencia de Plantillas
Todas las plantillas extienden el motor común `base.document` o están construidas de forma autónoma importando los estilos compartidos:
- `shared/print.css` (Phase 014)
- `outbound/shared/outbound.css` (Phase 018)
- `dispatch/shared/dispatch.css` (Phase 018)

## Jerarquía de Plantillas y Herencia
```mermaid
graph TD
    Base[base.document] --> OutboundBase[outbound_base.html]
    Base --> DispatchBase[dispatch_base.html]
    OutboundBase --> PED[ped_v1.html]
    OutboundBase --> ODS[ods_v1.html]
    OutboundBase --> PICK[pick_v1.html]
    OutboundBase --> PACK[pack_v1.html]
    DispatchBase --> MAN[man_v1.html]
    DispatchBase --> ADSP[adsp_v1.html]
    DispatchBase --> CPR[cpr_v1.html]
```
