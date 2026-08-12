# 04 — CPV: Control de Puerta Vehicular

## Propósito
El **CPV** registra el evento de ingreso o salida de un vehículo en la puerta del almacén: verificación de identidad del conductor, estado del precinto y decisión de acceso.

## Campos Clave

| Campo | Descripción |
|---|---|
| `gate_event_type` | Tipo de evento: INGRESO / SALIDA |
| `arrival_at` | Timestamp de llegada al gate |
| `gate` | Puerta o acceso utilizado |
| `gate_operator` | Operador que autoriza el acceso |
| `access_decision` | AUTORIZADO / RECHAZADO / EN_ESPERA |
| `appointment_reference` | CIT al que está asociado |
| `plate` | Placa del vehículo |
| `vehicle_type` | Tipo de vehículo (Camión, Furgoneta, etc.) |
| `driver_name` | Nombre del conductor |
| `driver_dni_raw` | DNI real (solo en backend, nunca se expone) |
| `driver_license_raw` | Nro. de licencia real (solo en backend) |
| `carrier_name` | Transportista |
| `seal_number` | Número de precinto observado |
| `seal_status` | COINCIDE / ROTO / NO_COINCIDE |

## Privacidad — Enmascaramiento Obligatorio
`driver_dni_raw` y `driver_license_raw` **nunca aparecen en el PDF renderizado**. El método `get_masked_context()` de `InboundCpvContext` los reemplaza antes de pasar el contexto a Jinja2:

```python
driver_dni_masked  = "******42"      # solo 2 dígitos finales visibles
driver_license_masked = "*******21"  # solo 2 dígitos finales visibles
```

## Integración Futura
- Control físico de acceso (RFID, barrera automatizada) — Fase 042+
- Registro de salidas vehiculares post-descarga
