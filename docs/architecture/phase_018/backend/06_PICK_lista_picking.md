# PICK — Lista de Picking (Phase 018)

## Propósito
Indica al operador del almacén qué artículos recoger, en qué ubicaciones y en qué orden de recorrido.

## Excepciones de Picking
Permite documentar discrepancias físicas en el almacén como `STOCK_NOT_FOUND`, `LOCATION_EMPTY`, etc.

## Flujo de Excepciones
```mermaid
graph TD
    Start[Operador en ubicación] -->|Escanea Producto| Compare{¿Stock disponible?}
    Compare -->|Sí| Confirm[Confirmar y continuar]
    Compare -->|No| Exc[Excepción: STOCK_NOT_FOUND]
    Exc -->|Acción Tomada| Log[Registrar en Acta de Excepciones]
```
