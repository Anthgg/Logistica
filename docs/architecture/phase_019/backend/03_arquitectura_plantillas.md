# Arquitectura de Plantillas (Phase 019)

## Herencia de Plantillas
Todas las plantillas extienden el motor común `base.document` o están construidas de forma autónoma importando los estilos compartidos:
- `shared/print.css`
- `transport/shared/transport.css`
- `delivery/shared/delivery.css`

## Jerarquía de Plantillas y Herencia
```mermaid
graph TD
    Base[base.document] --> TransportShared[transport.css]
    Base --> DeliveryShared[delivery.css]
    TransportShared --> HV[hv_v1.html]
    TransportShared --> HR[hr_v1.html]
    TransportShared --> CVT[cvt_v1.html]
    TransportShared --> PAR[par_v1.html]
    TransportShared --> INC[inc_v1.html]
    DeliveryShared --> POD[pod_v1.html]
    DeliveryShared --> EP[ep_v1.html]
    DeliveryShared --> RECH[rech_v1.html]
```
