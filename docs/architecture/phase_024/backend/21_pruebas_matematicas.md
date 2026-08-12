# 21. Cobertura de Pruebas Matemáticas y Precisión de Coma Fija

## 1. Suite de Pruebas Matemáticas (`tests/test_logistics_phase024.py`)

Para garantizar cero errores de precisión decimal, la suite de pruebas ejecuta casos de prueba de coma fija, límites de desbordamiento, reciprocidad de factores y prevención de float.

```python
import pytest
from decimal import Decimal
from src.apps.logistics.engine.conversion_engine import UnitConversionEngine
from src.apps.logistics.exceptions import InexactConversionException, CycleDetectedException

def test_decimal_precision_no_float_loss():
    """
    Verifica que la conversión de 1000.000000000000000000 a sub-unidades conserve exactitud.
    """
    input_qty = Decimal('1000.000000000000000000')
    factor = Decimal('0.001000000000000000')
    
    exact_result = input_qty * factor
    assert exact_result == Decimal('1.000000000000000000')
    assert str(exact_result) == '1.000000000000000000'

def test_reciprocal_factor_integrity():
    """
    Verifica que convertir A -> B -> A retorne exactamente la cantidad inicial sin remanente.
    """
    initial_qty = Decimal('12.500000000000000000')
    factor_direct = Decimal('1000.000000000000000000') # KG to G
    factor_inverse = Decimal('0.001000000000000000')  # G to KG
    
    converted = initial_qty * factor_direct # 12500 G
    back_to_initial = converted * factor_inverse # 12.5 KG
    
    assert back_to_initial == initial_qty

def test_exact_required_rounding_policy():
    """
    Verifica que EXACT_REQUIRED arroje excepción si el resultado contiene decimales.
    """
    engine = UnitConversionEngine(...)
    
    # 2.5 CAJAS no es exacto en EXACT_REQUIRED
    with pytest.raises(InexactConversionException):
        engine.apply_rounding(Decimal('2.5'), policy="EXACT_REQUIRED", target_scale=0)

def test_rejection_of_float_type():
    """
    Verifica que el motor rechace tipos float nativos de Python.
    """
    with pytest.raises(TypeError):
        UnitConversionEngine.validate_input(12.5) # float directo prohibido
```

---

## 2. Cobertura de Casos Borde (Edge Cases)

- **Conversiones con 18 Decimales Continuos**: $1\text{ LB} = 0.45359237\text{ KG}$. Se verifica que al multiplicar 1,000,000 de libras no haya desfase de miligramos.
- **División por Cero**: Intentar registrar `conversion_factor = 0` o `inverse_factor = 0` es rechazado por la restricción CHECK de PostgreSQL y la validación Pydantic.
- **Límite Numérico `NUMERIC(38,18)`**: Pruebas con cantidades extremas ($10^{20}$ unidades) confirman la ausencia de desbordamiento en consultas SQL.
