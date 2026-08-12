# 12. Especificación de Políticas de Redondeo Explícito (`RoundingPolicy`)

## 1. Definición del Enum `RoundingPolicy`

En la operativa real de un almacén, convertir unidades continuas a empaques discretos requiere reglas de redondeo explícitas y predecibles. El motor provee el enumerado `RoundingPolicy` para controlar este comportamiento según la intención del proceso logístico.

### Tabla de Políticas de Redondeo Soportadas:

| Clave Enum | Nombre Comercial | Comportamiento Matemático | Caso de Uso Logístico |
| :--- | :--- | :--- | :--- |
| `NONE` | Sin Redondeo | Mantiene la precisión completa a 18 decimales. | Valoraciones de costo contable e inventario base. |
| `EXACT_REQUIRED` | Redondeo Exacto | Exige que el resultado sea entero/exacto sin remanente. Si hay residuo, arroja error. | Picking de cajas cerradas sin apertura. |
| `HALF_UP` | Redondeo Estándar | Redondea al entero/escala más cercano. Si termina en $.5$, sube al superior. | Operativa comercial estándar. |
| `HALF_EVEN` | Redondeo Bancario | Redondea al par más cercano (Banker's Rounding). Minimiza sesgo estadístico. | Liquidación de fletes y auditoría masiva. |
| `FLOOR` | Hacia Abajo ($\lfloor x \rfloor$) | Trunca hacia el entero/escala inferior (hacia $-\infty$). | Cálculo de capacidad máxima de carga en contenedores. |
| `CEILING` | Hacia Arriba ($\lceil x \rceil$) | Ajusta al entero/escala superior (hacia $+\infty$). | Reserva conservadora de espacio y material de empaque. |
| `DOWN` | Truncamiento simple | Trunca los decimales sobrantes hacia cero. | Despacho estricto por lote. |
| `UP` | Redondeo absoluto arriba | Redondea alejándose de cero si hay cualquier decimal. | Cálculo de compras requeridas. |

---

## 2. Implementación de Políticas en `RoundingPolicyService`

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_FLOOR, ROUND_CEILING, ROUND_DOWN, ROUND_UP
from enum import Enum

class RoundingPolicy(str, Enum):
    NONE = "NONE"
    EXACT_REQUIRED = "EXACT_REQUIRED"
    HALF_UP = "HALF_UP"
    HALF_EVEN = "HALF_EVEN"
    FLOOR = "FLOOR"
    CEILING = "CEILING"
    DOWN = "DOWN"
    UP = "UP"

class InexactConversionException(Exception):
    pass

class RoundingPolicyService:
    @staticmethod
    def apply_rounding(value: Decimal, policy: RoundingPolicy, target_scale: int = 0) -> Decimal:
        if policy == RoundingPolicy.NONE:
            return value

        quantizer = Decimal('10') ** (-target_scale) if target_scale > 0 else Decimal('1')

        if policy == RoundingPolicy.EXACT_REQUIRED:
            rounded = value.quantize(quantizer, rounding=ROUND_HALF_UP)
            if value != rounded:
                raise InexactConversionException(
                    f"La conversión dio {value}, lo cual no es exacto para el requerimiento EXACT_REQUIRED."
                )
            return rounded
        elif policy == RoundingPolicy.HALF_UP:
            return value.quantize(quantizer, rounding=ROUND_HALF_UP)
        elif policy == RoundingPolicy.HALF_EVEN:
            return value.quantize(quantizer, rounding=ROUND_HALF_EVEN)
        elif policy == RoundingPolicy.FLOOR:
            return value.quantize(quantizer, rounding=ROUND_FLOOR)
        elif policy == RoundingPolicy.CEILING:
            return value.quantize(quantizer, rounding=ROUND_CEILING)
        elif policy == RoundingPolicy.DOWN:
            return value.quantize(quantizer, rounding=ROUND_DOWN)
        elif policy == RoundingPolicy.UP:
            return value.quantize(quantizer, rounding=ROUND_UP)
        
        return value
```

---

## 3. Matriz de Ejemplos de Evaluación

Dado un resultado exacto calculado $x = 12.3456$:

| Política | `target_scale = 0` (Enteros) | `target_scale = 2` |
| :--- | :--- | :--- |
| `HALF_UP` | `12` | `12.35` |
| `HALF_EVEN` | `12` | `12.35` |
| `FLOOR` | `12` | `12.34` |
| `CEILING` | `13` | `12.35` |
| `DOWN` | `12` | `12.34` |
| `UP` | `13` | `12.35` |
| `EXACT_REQUIRED` | Error `InexactConversionException` | Error `InexactConversionException` |
