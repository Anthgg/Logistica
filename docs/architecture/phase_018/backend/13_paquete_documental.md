# Paquete Documental (Phase 018)

## Modos del Paquete
Consolida múltiples documentos según la etapa del despacho:
- `OUTBOUND_REQUEST`: PED
- `OUTBOUND_AUTHORIZATION`: PED + ODS
- `PICKING`: ODS + PICK
- `PACKING`: ODS + PICK + PACK
- `DISPATCH`: MAN + ADSP
- `TRANSPORT_HANDOFF`: MAN + ADSP + CPR

## Flujo de Generación de Preview Conjunto
```mermaid
graph LR
    Payload[Payload Paquete] --> Valid[PackageHierarchyValidator]
    Valid --> Manifest[Generación Manifiesto JSON]
    Manifest --> Combine[Preview Conjunto PDF Multipágina]
```
