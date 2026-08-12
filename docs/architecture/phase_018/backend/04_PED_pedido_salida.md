# PED — Pedido de Salida (Phase 018)

## Propósito
El Pedido de Salida (PED) representa una solicitud formal (interna o de cliente) para retirar mercancía de un almacén. No autoriza físicamente el retiro ni reserva inventario.

## Flujo PED → ODS → PICK → PACK
```mermaid
graph LR
    PED[PED: Solicitud] -->|Aprobación| ODS[ODS: Autorización]
    ODS -->|Asignación Recorrido| PICK[PICK: Lista Picking]
    PICK -->|Consolidación Bultos| PACK[PACK: Packing List]
```

## Campos y Validaciones
- **Campos**: Solicitante, prioridad, fecha requerida, motivo, dirección de destino.
- **Validaciones**: Requiere al menos una línea con cantidad mayor a cero.
- **Límite**: `PENDING_PHASE_051` (no crea pedidos reales).
