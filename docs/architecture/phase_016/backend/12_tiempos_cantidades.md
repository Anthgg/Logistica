# 12 — Tiempos y Cantidades

## Campos de Tiempo en Documentos de Ingreso

| Documento | Campo | Formato | Descripción |
|---|---|---|---|
| CIT | `appointment_date` | `YYYY-MM-DD` | Fecha de la cita |
| CIT | `appointment_window_start/end` | `HH:MM` | Ventana horaria (ej. 08:00–10:00) |
| CPV | `arrival_at` | ISO 8601 UTC | Timestamp exacto de llegada al gate |
| AREC | `unloading_start` / `unloading_end` | `HH:MM:SS` | Inicio y fin de descarga |
| DIF | `report_date` | ISO 8601 UTC | Timestamp del reporte de diferencias |
| NC | `detection_date` | ISO 8601 UTC | Timestamp del hallazgo de calidad |

Todos los timestamps se almacenan en **UTC**. La plantilla Jinja2 recibe `now` como `datetime.now(timezone.utc)` y lo usa como fallback cuando el campo no se provee.

## Campos de Cantidad — Tipo `Decimal`

Todos los campos de cantidad usan `Decimal` (no `float`) para evitar errores de punto flotante:

```python
class InboundItemSchema(BaseModel):
    expected_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    received_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    accepted_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    rejected_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    unit: str = "UND"
```

### Invariante de integridad
> `received_quantity == accepted_quantity + rejected_quantity`

Esta invariante **no se valida en Fase 016** (modo preview). Se validará en Fase 041 cuando el AREC sea un documento oficial con efecto real en inventario.

## Unidades Soportadas
`UND`, `KG`, `LT`, `MT`, `CAJA`, `PALET`, `ROLLO`, `BOLSA`
