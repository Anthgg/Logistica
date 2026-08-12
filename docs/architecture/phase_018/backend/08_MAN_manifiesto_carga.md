# MAN — Manifiesto de Carga (Phase 018)

## Propósito
Consolida el viaje agrupando pedidos, bultos y destinos asignados a un vehículo de transporte específico.

## Validación de Capacidad Vehicular
Calcula la tasa de utilización y alerta sobrecapacidad utilizando la clase `CapacityCalculator`.

## Flujo PACK → MAN → ADSP
```mermaid
graph LR
    PACK[PACK: Bultos Consolidados] -->|Asignar a Viaje| MAN[MAN: Manifiesto Carga]
    MAN -->|Carga en Muelle| ADSP[ADSP: Acta Despacho]
```
