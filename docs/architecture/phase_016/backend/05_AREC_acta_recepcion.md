# 05 — AREC: Acta de Recepción

## Propósito
El **AREC** es el documento central del proceso de recepción. Registra formalmente la descarga, el conteo físico de productos y el resultado general de la recepción (ACEPTADO / ACEPTADO_CON_DIFERENCIAS / RECHAZADO).

## Campos Clave

| Campo | Descripción |
|---|---|
| `reception_date` | Fecha del evento de recepción |
| `warehouse` / `dock` | Almacén y muelle utilizados |
| `unloading_start` / `unloading_end` | Tiempos de inicio y fin de descarga |
| `supplier_name` | Proveedor |
| `purchase_order_reference` | OC referenciada |
| `reception_result` | ACEPTADO / ACEPTADO_CON_DIFERENCIAS / RECHAZADO |
| `waybill_reference` | Guía de remisión del transportista |
| `received_items[]` | Tabla de líneas con cantidades |

## Tabla de Cantidades

Cada línea de `received_items` contiene:

| Sub-campo | Tipo | Descripción |
|---|---|---|
| `expected_quantity` | `Decimal` | Cantidad esperada según OC |
| `received_quantity` | `Decimal` | Cantidad físicamente descargada |
| `accepted_quantity` | `Decimal` | Cantidad aceptada para ingreso |
| `rejected_quantity` | `Decimal` | Cantidad rechazada (daño, vencimiento, etc.) |

Todos los campos usan `Decimal` con `ge=0` para evitar cantidades negativas.

## Relaciones Documentales
- **Referencia hacia:** CIT, CPV (previos en el flujo)
- **Genera hacia:** NI (si hay aceptados), DIF (si hay diferencias), NC (si hay no conformidades de calidad)
