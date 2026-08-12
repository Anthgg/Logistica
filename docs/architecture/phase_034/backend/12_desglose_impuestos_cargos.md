# 12 — Desglose de Impuestos, Fletes y Cargos (`po_*_tax_components` / `po_*_charges`)

---

## 1. Tratamiento Impositivo y Financiero Avanzado

En compras locales e internacionales, la facturación no se limita únicamente al precio base del producto y al impuesto a las ventas (IGV). Requiere estructurar conceptos como retenciones de impuestos, detracciones del sistema SPOT (SUNAT en Perú), fletes logísticos, seguros de carga y cargos de manipuleo.

La Fase 034 descompone estos conceptos en dos modelos ORM dedicados:

1. **`PurchaseOrderTaxComponentModel`** (`po_purchase_order_tax_components`): Almacena componentes fiscales a nivel de línea o documento.
2. **`PurchaseOrderChargeModel`** (`po_purchase_order_charges`): Almacena cargos adicionales o descuentos globales.

---

## 2. Modelo ORM `po_purchase_order_tax_components`

```sql
CREATE TABLE po_purchase_order_tax_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_line_id UUID REFERENCES po_purchase_order_lines(id) ON DELETE RESTRICT,
    revision_id UUID NOT NULL REFERENCES po_purchase_order_revisions(id) ON DELETE RESTRICT,
    tax_type VARCHAR(32) NOT NULL, -- 'IGV', 'ISC', 'DETRACCION', 'RETENCION_IR'
    tax_rate NUMERIC(28, 10) NOT NULL,
    taxable_base NUMERIC(28, 10) NOT NULL,
    tax_amount NUMERIC(28, 10) NOT NULL,
    is_retention BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_tax_rate CHECK (tax_rate >= 0 AND tax_rate <= 100),
    CONSTRAINT ck_po_tax_amount_non_neg CHECK (tax_amount >= 0)
);
```

### Tipos de Impuestos Soportados (`tax_type`):
* **`IGV`**: Impuesto General a las Ventas (tasa estándar 18.00%).
* **`ISC`**: Impuesto Selectivo al Consumo.
* **`DETRACCION`**: Sistema de Pago de Obligaciones Tributarias (SPOT) aplicable a servicios y bienes regulados (e.g. 4%, 10%, 12%).
* **`RETENCION_IR`**: Retención del Impuesto a la Renta de No Domiciliados (compras internacionales).

---

## 3. Modelo ORM `po_purchase_order_charges`

```sql
CREATE TABLE po_purchase_order_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id UUID NOT NULL REFERENCES po_purchase_order_revisions(id) ON DELETE RESTRICT,
    charge_type VARCHAR(32) NOT NULL, -- 'FREIGHT', 'INSURANCE', 'PACKAGING', 'GLOBAL_DISCOUNT', 'HANDLING'
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(28, 10) NOT NULL,
    currency_code VARCHAR(3) NOT NULL,
    is_additive BOOLEAN NOT NULL DEFAULT TRUE, -- TRUE para cargos (fletes), FALSE para descuentos globales
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 4. Algoritmo de Integridad de Totales con Cargos e Impuestos

El servicio de dominio valida que la suma vectorial de los componentes impositivos y cargos coincida exactamente con los campos de cabecera del `monetary_snapshot`:

$$\text{GrandTotal} = \text{NetSubtotal} + \sum \text{TaxAmount}_{\text{aditivos}} - \sum \text{TaxAmount}_{\text{retenciones}} + \sum \text{Charges}_{\text{aditivos}} - \sum \text{Charges}_{\text{deductivos}}$$

```python
def validate_financial_breakdown_integrity(monetary_snapshot: Dict[str, Any], tax_components: list, charges: list) -> None:
    calculated_tax = sum(c.tax_amount for c in tax_components if not c.is_retention)
    calculated_charges = sum(ch.amount for ch in charges if ch.is_additive)
    calculated_discounts = sum(ch.amount for ch in charges if not ch.is_additive)
    
    expected_total = (
        Decimal(monetary_snapshot["net_subtotal"]) + 
        calculated_tax + 
        calculated_charges - 
        calculated_discounts
    )
    
    actual_total = Decimal(monetary_snapshot["grand_total"])
    if expected_total != actual_total:
        raise FinancialIntegrityError(
            f"Mismatch in grand total calculation: expected {expected_total}, got {actual_total}"
        )
```
