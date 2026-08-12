# Validaciones y Coherencia (Phase 018)

## Flujo de Cantidades
```mermaid
graph LR
    REQ[Requested] -->|Approved| APP[Approved]
    APP -->|Allocated| ALC[Allocated]
    ALC -->|Picked| PIK[Picked]
    PIK -->|Packed| PAK[Packed]
    PAK -->|Loaded| LOD[Loaded]
```

## Reglas de Negocio
- `approved_quantity <= requested_quantity`
- `allocated_quantity <= approved_quantity`
- `picked_quantity <= allocated_quantity`
- `packed_quantity <= picked_quantity`
- `loaded_quantity <= packed_quantity`
- `gross_weight >= net_weight`
