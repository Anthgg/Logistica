# Validaciones de Cantidades (Phase 017)

## Tipos de Datos
Todas las cantidades de inventario se validan y operan con el tipo de datos `Decimal` con escala de dos decimales para evitar errores de coma flotante.

## Reglas de Negocio Ejecutadas
1. **Cantidades Positivas**: Lotes a transferir o mover deben tener cantidades mayores a cero (`gt=0`).
2. **Coherencia en Ajustes**: `recorded_quantity + adjustment_quantity = verified_quantity`.
3. **Coherencia en Recepción**: `accepted + observed + rejected <= received`.
4. **Cálculo de Diferencias en CRT**:
   - `shortage = max(0, dispatched - received)`
   - `overage = max(0, received - dispatched)`
