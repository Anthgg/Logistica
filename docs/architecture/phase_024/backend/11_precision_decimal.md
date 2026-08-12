# 11. Política de Precisión Matemática Decimal (`NUMERIC(38,18)`)

## 1. Justificación Matemática del Estándar `NUMERIC(38,18)`

Los sistemas logísticos y financieros de alto volumen sufren acumulaciones de errores por redondeo cuando utilizan tipos de datos imprecisos. Para erradicar este problema, la **Fase 024** estandariza el almacenamiento y procesamiento numérico en **`NUMERIC(38,18)`** (o `DECIMAL(38,18)` en PostgreSQL).

### Definición de Capacidad:
- **38 Dígitos Totales de Precisión**: Permite representar valores enteros de hasta 20 dígitos ($10^{20}$ unidades), adecuados para volúmenes masivos de inventario global.
- **18 Dígitos Decimales de Escala**: Garantiza representar fracciones hasta $10^{-18}$ (sub-microgramos o nanómetros), eliminando cualquier pérdida de información por conversión.

---

## 2. Configuración en Python (`decimal.Decimal`)

En la capa de aplicación Python / FastAPI, todo valor numérico de conversión se procesa exclusivamente con el módulo `decimal` de la librería estándar, configurando el contexto global a 38 dígitos de precisión:

```python
import decimal

# Configuración del Contexto de Precisión Decimal Global
DECIMAL_CONTEXT = decimal.Context(prec=38, rounding=decimal.ROUND_HALF_UP)
decimal.setcontext(DECIMAL_CONTEXT)

def safe_decimal(value: Union[str, int, Decimal]) -> Decimal:
    """
    Convierte de forma segura cualquier entrada a Decimal de 38,18.
    Queda prohibido pasar tipos 'float' directamente.
    """
    if isinstance(value, float):
        raise TypeError(
            "Uso ilegal de tipo 'float' detectado en el motor de conversiones. "
            "Pase cadenas de texto str() o int() para construir Decimal."
        )
    return Decimal(str(value))
```

---

## 3. Serialización String en Respuestas JSON (REST APIs)

Dado que JavaScript/JSON parsea los números no entrecomillados como números IEEE-754 de 64 bits (perdiendo precisión a partir de los 15-17 dígitos significativos), **todos los campos de cantidad y factores de conversión en las APIs REST se serializan estrictamente como Strings**.

### Ejemplo de Payloads JSON:

```json
{
  "from_unit_code": "KG",
  "to_unit_code": "G",
  "input_quantity": "12.500000000000000000",
  "exact_result": "12500.000000000000000000",
  "effective_factor": "1000.000000000000000000",
  "residual": "0.000000000000000000"
}
```

### Esquema de Validación Pydantic (v2):

```python
from pydantic import BaseModel, field_serializer
from decimal import Decimal

class ConversionResponseSchema(BaseModel):
    input_quantity: Decimal
    exact_result: Decimal
    effective_factor: Decimal
    residual: Decimal

    @field_serializer('input_quantity', 'exact_result', 'effective_factor', 'residual')
    def serialize_decimal_to_str(self, value: Decimal, _info) -> str:
        return f"{value:.18f}"
```
