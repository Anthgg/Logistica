# 13 — Programación de Entregas Parciales (`po_*_delivery_schedules`)

---

## 1. Planificación de Despachos y Entregas Escalonadas

En órdenes de gran volumen o contratos marco, el proveedor no despacha la totalidad de los ítems en una única fecha o dirección. La entrega se distribuye en cronogramas semanales o mensuales dirigidos a distintos almacenes de la empresa.

Para soportar esta complejidad operativa, la Fase 034 implementa la programación de entregas parciales mediante dos modelos ORM:

1. **`PurchaseOrderDeliveryScheduleModel`** (`po_purchase_order_delivery_schedules`): Cabecera del plan de entregas de la OC.
2. **`PurchaseOrderDeliveryScheduleLineModel`** (`po_purchase_order_delivery_schedule_lines`): Desglose de cantidades por ítem, fecha comprometida, almacén destino y ventana horaria.

---

## 2. Modelos ORM de Entregas Parciales

### 2.1. Cabecera del Cronograma (`po_purchase_order_delivery_schedules`)
```sql
CREATE TABLE po_purchase_order_delivery_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES po_purchase_orders(id) ON DELETE RESTRICT,
    revision_id UUID NOT NULL REFERENCES po_purchase_order_revisions(id) ON DELETE RESTRICT,
    schedule_code VARCHAR(32) NOT NULL,
    incoterm VARCHAR(16) NOT NULL DEFAULT 'DDP', -- Incoterms 2020: DDP, FOB, CIF, EXW
    total_deliveries_count INT NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.2. Detalle de Entregas (`po_purchase_order_delivery_schedule_lines`)
```sql
CREATE TABLE po_purchase_order_delivery_schedule_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_schedule_id UUID NOT NULL REFERENCES po_purchase_order_delivery_schedules(id) ON DELETE RESTRICT,
    purchase_order_line_id UUID NOT NULL REFERENCES po_purchase_order_lines(id) ON DELETE RESTRICT,
    delivery_batch_number INT NOT NULL,
    scheduled_quantity NUMERIC(28, 10) NOT NULL,
    expected_delivery_date DATE NOT NULL,
    time_window_start TIME,
    time_window_end TIME,
    destination_warehouse_id UUID NOT NULL,
    destination_address TEXT NOT NULL,
    contact_person_name VARCHAR(128),
    contact_phone VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_delivery_scheduled_qty_pos CHECK (scheduled_quantity > 0),
    CONSTRAINT ck_po_delivery_status CHECK (status IN ('SCHEDULED', 'IN_TRANSIT', 'PARTIALLY_DELIVERED', 'COMPLETED', 'CANCELLED'))
);
```

---

## 3. Reglas de Validación de Dominio para Entregas

### Regla 1: Coincidencia Exacta de Cantidades Programadas
La suma de las cantidades programadas en los lotes de entrega debe ser exactamente igual a la cantidad total pedida en la línea de la OC:

$$\sum_{i=1}^{n} \text{scheduled\_quantity}_i = \text{ordered\_quantity}$$

```python
def validate_delivery_schedule_balance(po_line_id: UUID, ordered_qty: Decimal, schedule_lines: list) -> None:
    sum_scheduled = sum(line.scheduled_quantity for line in schedule_lines if line.purchase_order_line_id == po_line_id)
    if sum_scheduled != ordered_qty:
        raise DeliveryScheduleBalanceError(
            f"Scheduled quantity sum ({sum_scheduled}) does not match ordered line quantity ({ordered_qty})"
        )
```

### Regla 2: Ventana Horaria Válida
Si se definen los campos `time_window_start` y `time_window_end`, la hora de inicio debe ser estrictamente anterior a la hora de fin (`time_window_start < time_window_end`).
