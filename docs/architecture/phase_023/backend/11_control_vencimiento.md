# 11 — Configuración de Control de Vencimiento y Vida Útil

## 1. Definición del Control de Caducidad

En industrias como la alimentaria, farmacéutica y química, el control de la fecha de caducidad/expiración es un requisito crítico para garantizar la calidad del producto y la seguridad del consumidor. 

La **Fase 023** establece los parámetros de configuración de la vida útil en la entidad de producto, permitiendo definir la durabilidad total en días, los márgenes mínimos aceptables para recepción de proveedores y las reglas de rotación recomendadas (FEFO - *First Expired, First Out*).

---

## 2. Parámetros de Vencimiento en la Política de Dominio

Los atributos de vida útil y vencimiento se modelan dentro de la estructura de políticas y perfil de producto:

```sql
CREATE TYPE expiration_control_type_enum AS ENUM (
    'NOT_APPLICABLE',   -- El producto no vence (ej. herramientas, tornillos)
    'OPTIONAL',         -- Vencimiento opcional
    'MANDATORY',        -- Vencimiento obligatorio en cada lote
    'DERIVED_FROM_LOT'  -- La fecha de vencimiento se calcula automáticamente según la fecha de fabricación
);

ALTER TABLE product_tracking_policies
    ADD COLUMN expiration_control expiration_control_type_enum NOT NULL DEFAULT 'NOT_APPLICABLE',
    ADD COLUMN total_shelf_life_days INTEGER NULL,     -- Vida útil total desde fabricación (días)
    ADD COLUMN minimum_shelf_life_days INTEGER NULL,   -- Mínimo de vida útil remanente exigida al recibir de proveedor
    ADD COLUMN outbound_min_shelf_life_days INTEGER NULL; -- Mínimo de vida útil remanente para despachar a cliente
```

---

## 3. Lógica de Validación de Días de Vida Útil

```python
class ShelfLifeValidationError(ValueError):
    pass

class ProductShelfLifeValidator:

    @classmethod
    def validate_shelf_life(
        cls,
        expiration_control: str,
        total_days: int | None,
        min_inbound_days: int | None,
        min_outbound_days: int | None
    ):
        if expiration_control == "NOT_APPLICABLE":
            return
            
        if expiration_control in ["MANDATORY", "DERIVED_FROM_LOT"]:
            if total_days is None or total_days <= 0:
                raise ShelfLifeValidationError(
                    f"Para el control de vencimiento '{expiration_control}', los días totales de vida útil ('total_shelf_life_days') deben ser mayores a 0."
                )
                
            if min_inbound_days is not None:
                if min_inbound_days > total_days:
                    raise ShelfLifeValidationError(
                        "La vida útil mínima de recepción de proveedores ('minimum_shelf_life_days') no puede ser mayor a la vida útil total del producto."
                    )
                    
            if min_outbound_days is not None:
                if min_outbound_days > total_days:
                    raise ShelfLifeValidationError(
                        "La vida útil mínima de despacho ('outbound_min_shelf_life_days') no puede ser mayor a la vida útil total."
                    )
```

---

## 4. Diagrama de Reglas de Vida Útil en Cadena de Suministro

```
+-----------------------------------------------------------------------------------+
|                        FECHA DE FABRICACIÓN / ENVASADO                            |
+-----------------------------------------------------------------------------------+
  |                                                                               |
  | <-- minimum_shelf_life_days --> |                                             |
  |   (Ventana Aceptable Recepción) |                                             |
  v                                 v                                             v
[FECHA FABRICACIÓN] -----------> [LÍMITE RECEPCIÓN] --------------------> [FECHA CADUCIDAD]
                                                               (total_shelf_life_days)
```

### Ejemplo Práctico (Yogurt Lácteo):
- `total_shelf_life_days`: **45 días** (Vida útil total).
- `minimum_shelf_life_days`: **30 días**. Si el proveedor entrega un lote con solo 20 días restantes de vida útil, el sistema WMS rechazará automáticamente la recepción en muelle (*Dock*).
- `outbound_min_shelf_life_days`: **15 días**. Si un lote tiene menos de 15 días de vida útil, se bloquea automáticamente para pedidos de clientes y se desvía a área de remate o merma.

---

## 5. Desacoplamiento de Lotes Reales

Al igual que las políticas de lote y serie, las fechas de caducidad reales ($\text{Expiration Date} = \text{Manufacturing Date} + \text{total\_shelf\_life\_days}$) se asignarán dinámicamente a las instancias de inventario durante las pruebas de recepción de la **Fase 046**.
