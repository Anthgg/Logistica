# 06 — NI: Nota de Ingreso a Almacén

## Propósito
La **NI** (Nota de Ingreso) formaliza que los productos aceptados en el AREC quedan registrados como pendientes de putaway en el almacén. En Fase 016 **NO crea movimientos de stock reales** — ese proceso queda diferido a las Fases 041–046.

## Campos Clave

| Campo | Descripción |
|---|---|
| `entry_date` | Fecha de registro del ingreso |
| `warehouse` | Almacén receptor |
| `reception_reference` | AREC al que está vinculada |
| `quality_state` | Estado de calidad: APROBADO_SINO_INSPECCION, EN_INSPECCION, BLOQUEADO |
| `inventory_state` | Estado de inventario: **PENDIENTE_PUTAWAY** (en esta fase) |
| `responsible_user` | Jefe de almacén responsable |
| `accepted_items[]` | Productos y cantidades aceptadas para ingreso |

## Límite de Fase — Sin Stock
> ⚠️ La NI en Fase 016 es un documento de intención. El inventario real se crea en Fases 041–046 cuando se confirme el putaway físico.

## Relaciones Documentales
- **Depende de:** AREC (solo se genera si `accepted_quantity > 0`)
- **Precede a:** Módulo de Putaway (Fase 043+)
