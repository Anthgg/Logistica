# CPR — Control de Precinto (Phase 018)

## Propósito
Registra y audita la colocación, verificación e integridad de los precintos de seguridad aplicados a la carga del vehículo.

## Historial de Eventos del Precinto
```mermaid
graph TD
    APPLIED[APPLIED: Aplicado en muelle] --> VERIFIED[VERIFIED: Validado en puerta]
    VERIFIED -->|Incidencia| BROKEN[BROKEN: Precinto roto]
    BROKEN -->|Autorizado| REPLACED[REPLACED: Reemplazado]
```
