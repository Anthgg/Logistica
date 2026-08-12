# ADSP — Acta de Despacho (Phase 018)

## Propósito
Documento de cierre que certifica el resultado de la carga física y la salida del camión de la sede.

## Flujo ADSP → CPR
```mermaid
graph LR
    ADSP[ADSP: Acta Despacho] -->|Inspección Puerta| CPR[CPR: Control de Precinto]
```

## Campos y Validaciones
- **Campos**: Tiempos de inicio y fin de carga, unidades esperadas vs cargadas, firmas.
- **Validaciones**: Se rechaza si la hora de fin de carga es previa a la hora de inicio.
