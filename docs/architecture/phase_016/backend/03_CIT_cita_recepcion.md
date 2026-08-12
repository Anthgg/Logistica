# 03 — CIT: Cita de Recepción

## Propósito
El documento **CIT** (Cita de Recepción) programa formalmente la llegada de un vehículo proveedor al almacén, definiendo la ventana horaria, el muelle asignado y la carga esperada.

## Campos Clave

| Campo | Descripción |
|---|---|
| `appointment_date` | Fecha programada de llegada |
| `appointment_window_start` / `_end` | Ventana horaria asignada (ej. 08:00–10:00) |
| `warehouse` | Almacén receptor |
| `dock` | Muelle o puerta de descarga asignada |
| `purchase_order_reference` | OC relacionada |
| `operation_type` | Tipo de operación (RECEPCION_PROVEEDOR, DEVOLUCION, etc.) |
| `supplier_name` | Razón social del proveedor |
| `carrier_name` | Empresa de transporte |
| `expected_plate` | Placa del vehículo esperado |
| `expected_driver_name` | Nombre del conductor esperado |
| `expected_items[]` | Listado de productos y cantidades esperadas |

## Modo Preview
En Fase 016, el CIT opera exclusivamente en modo `PREVIEW` con marca de agua `VISTA PREVIA`. No se reservan correlativos ni se registran citas reales en base de datos.

## Integración Futura
- Fase 041+: Módulo de scheduling real con gestión de ventanas, bloqueos de muelle y confirmaciones de proveedor.
- El CIT se convierte en documento oficial al confirmar la cita con el proveedor.
