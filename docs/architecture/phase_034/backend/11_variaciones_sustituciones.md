# 11 — Variaciones y Sustituciones Justificadas (`po_purchase_order_source_variances`)

---

## 1. Control de Desviaciones entre Cotización y Orden Emitida

En la operativa real de aprovisionamiento, pueden presentarse diferencias técnicas o comerciales entre la propuesta ganadora adjudicada en el CCO y la Orden de Compra definitiva (e.g. descatalogación de SKU con reemplazo por modelo equivalente, ajuste menor de precio por empaque comercial, conversión de unidad de medida de *Cajas* a *Unidades*).

Para evitar alterar las cotizaciones históricas y mantener la transparencia técnica, la Fase 034 registra cada desviación en el modelo **`PurchaseOrderSourceVarianceModel`** (`po_purchase_order_source_variances`).

---

## 2. Estructura del Modelo ORM `po_purchase_order_source_variances`

```sql
CREATE TABLE po_purchase_order_source_variances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_line_id UUID NOT NULL REFERENCES po_purchase_order_lines(id) ON DELETE RESTRICT,
    variance_type VARCHAR(32) NOT NULL,
    original_value TEXT NOT NULL,
    new_value TEXT NOT NULL,
    justification TEXT NOT NULL,
    approved_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_variance_type CHECK (variance_type IN ('PRICE_DEVIATION', 'QUANTITY_DEVIATION', 'SKU_SUBSTITUTION', 'UOM_CONVERSION'))
);
```

---

## 3. Tipos de Variaciones Soportadas

| `variance_type` | Descripción del Escenario Operativo | Ejemplo de `original_value` $\rightarrow$ `new_value` |
| :--- | :--- | :--- |
| **`PRICE_DEVIATION`** | Desviación aprobada en el precio unitario pactado (e.g., actualización por tipo de cambio o flete extraordinario). | `USD 100.00` $\rightarrow$ `USD 102.50` |
| **`QUANTITY_DEVIATION`** | Ajuste menor en la cantidad solicitada debido a lotes mínimos de empaque del proveedor. | `100.0000000000 UN` $\rightarrow$ `120.0000000000 UN` |
| **`SKU_SUBSTITUTION`** | Sustitución justificada de un producto por descontinuación o actualización de código de fabricante. | `SKU-MOTOR-V1` $\rightarrow$ `SKU-MOTOR-V2` |
| **`UOM_CONVERSION`** | Cambio de la unidad de medida manteniendo el equivalente físico. | `10.0000000000 CJ` $\rightarrow$ `120.0000000000 UN` |

---

## 4. Reglas de Validación de Dominio

1. **Justificación Obligatoria**: El campo `justification` no puede estar vacío ni contener cadenas genéricas de menos de 10 caracteres.
2. **Autorización del Aprobador**: El campo `approved_by_user_id` debe registrar el ID del usuario autorizado que validó la variación antes del envío a aprobación.
3. **Inmutabilidad Auditada**: El registro de variaciones es estrictamente *append-only*; no se permiten actualizaciones o eliminaciones físicas.
