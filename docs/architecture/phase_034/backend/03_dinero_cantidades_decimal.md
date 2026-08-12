# 03 — Especificación de Dinero, Cantidades y Aritmética Exacta (`Decimal`)

---

## 1. Prohibición Absoluta de Coma Flotante (`float`)

En sistemas de aprovisionamiento y contabilidad financiera, el uso de tipos de datos de coma flotante nativos (`float` en Python o `FLOAT/DOUBLE` en bases de datos) introduce imprecisiones inherentes al estándar IEEE-754 (e.g. `0.1 + 0.2 = 0.30000000000000004`).

En la Fase 034 se establece una **regla de diseño estricta e inviolable**:

> **Queda estrictamente prohibido el uso del tipo `float` en cualquier entidad, Value Object, servicio o DTO para representar valores monetarios o cantidades.**
> 
> **Todos los valores monetarios y cuantitativos deben procesarse utilizando el tipo `Decimal` de la librería estándar `decimal` de Python y almacenarse como `Numeric(28,10)` en PostgreSQL.**

---

## 2. Value Objects del Dominio

### 2.1. Value Object `Money`
Representa una magnitud económica inmutable junto con su código ISO de moneda (e.g. `PEN`, `USD`, `EUR`).

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money amount must be Decimal, got {type(self.amount)}")
        if not self.currency_code or len(self.currency_code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code")

    def add(self, other: Money) -> Money:
        if self.currency_code != other.currency_code:
            raise CurrencyMismatchError(self.currency_code, other.currency_code)
        return Money(self.amount + other.amount, self.currency_code)

    def subtract(self, other: Money) -> Money:
        if self.currency_code != other.currency_code:
            raise CurrencyMismatchError(self.currency_code, other.currency_code)
        return Money(self.amount - other.amount, self.currency_code)
```

### 2.2. Value Object `QuantityAmount`
Representa la cantidad física de un ítem y su unidad de medida (UOM).

```python
@dataclass(frozen=True)
class QuantityAmount:
    value: Decimal
    unit_of_measure: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError(f"Quantity value must be Decimal, got {type(self.value)}")
        if self.value <= Decimal("0"):
            raise ValueError("Quantity value must be strictly positive")
```

---

## 3. Servicio de Cálculo Financiero (`PurchaseOrderMoneyService`)

El servicio `PurchaseOrderMoneyService` encapsula las fórmulas de cálculo monetario de líneas y resumen general de la Orden de Compra. Usa de forma predeterminada el modo de redondeo `decimal.ROUND_HALF_UP`.

### Fórmulas de Cálculo por Línea:

1. **Subtotal de Línea**:
   $$\text{line\_subtotal} = \text{ordered\_quantity} \times \text{unit\_price}$$

2. **Monto de Descuento de Línea**:
   * Si `discount_type == 'PERCENTAGE'`:
     $$\text{discount\_amount} = \text{line\_subtotal} \times \left( \frac{\text{discount\_value}}{100} \right)$$
   * Si `discount_type == 'FIXED'`:
     $$\text{discount\_amount} = \text{discount\_value}$$

3. **Subtotal Neto de Línea**:
   $$\text{line\_net} = \text{line\_subtotal} - \text{discount\_amount}$$

4. **Monto de Impuesto (IGV 18% u otro)**:
   $$\text{tax\_amount} = \text{line\_net} \times \left( \frac{\text{tax\_rate}}{100} \right)$$

5. **Total de Línea**:
   $$\text{line\_total} = \text{line\_net} + \text{tax\_amount} + \text{freight\_amount} + \text{other\_charges\_amount}$$

---

## 4. Ejemplo de Cálculo de Resumen General (`SummaryCalculationResult`)

```python
@dataclass(frozen=True)
class SummaryCalculationResult:
    subtotal: Decimal          # Suma de line_subtotal
    discount_total: Decimal    # Suma de discount_amount
    net_subtotal: Decimal      # Suma de line_net (subtotal - discount_total)
    tax_total: Decimal         # Suma de tax_amount
    freight_total: Decimal     # Suma de freight_amount
    charges_total: Decimal     # Suma de otros cargos
    grand_total: Decimal       # Total Final General
```

### Código de Verificación de Redondeo Bancario `ROUND_HALF_UP`:
```python
def quantize_currency(value: Decimal, scale: int = 2) -> Decimal:
    exponent = Decimal("10") ** (-scale)
    return value.quantize(exponent, rounding=ROUND_HALF_UP)
```
