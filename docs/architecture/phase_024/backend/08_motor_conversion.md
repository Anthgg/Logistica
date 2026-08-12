# 08. Motor de Conversiones de Unidades (`UnitConversionEngine`)

## 1. Especificación del Motor `UnitConversionEngine`

El servicio `UnitConversionEngine` es el componente central de cálculo matemático del sistema. Recibe solicitudes de conversión de cantidades entre dos unidades y ejecuta la evaluación matemática aplicando reglas de coma fija estricta (`Decimal` con precisión de 38 dígitos y 18 decimales).

### Arquitectura de Clases del Motor:

```python
class UnitConversionEngine:
    def __init__(
        self, 
        path_resolver: ConversionPathResolver, 
        rounding_service: RoundingPolicyService
    ):
        self.path_resolver = path_resolver
        self.rounding_service = rounding_service

    def evaluate_conversion(
        self, 
        request: ConversionRequestDTO
    ) -> ConversionResultDTO:
        # 1. Validar que la cantidad de entrada sea Decimal
        quantity = Decimal(str(request.quantity))
        
        # 2. Obtener la ruta y el factor de conversión acumulado
        path_result = self.path_resolver.find_conversion_path(
            from_unit_id=request.from_unit_id,
            to_unit_id=request.to_unit_id,
            product_id=request.product_id,
            organization_id=request.organization_id
        )
        
        # 3. Cálculo exacto sin redondeo (NUMERIC 38,18)
        exact_result = quantity * path_result.effective_factor
        
        # 4. Aplicar política de redondeo solicitada
        rounded_result = self.rounding_service.apply_rounding(
            value=exact_result,
            policy=request.rounding_policy,
            target_scale=request.target_scale
        )
        
        # 5. Cálculo del residual exacto
        # residual = input_quantity - (rounded_result / effective_factor)
        calculated_input_from_rounded = rounded_result / path_result.effective_factor
        residual = quantity - calculated_input_from_rounded

        return ConversionResultDTO(
            from_unit_id=request.from_unit_id,
            to_unit_id=request.to_unit_id,
            input_quantity=quantity,
            exact_result=exact_result,
            rounded_result=rounded_result,
            residual=residual,
            effective_factor=path_result.effective_factor,
            path_hops=path_result.hops,
            rounding_policy_applied=request.rounding_policy
        )
```

---

## 2. Eliminación Total del Tipo `float` (Desaprobación Restricta)

Queda **estrictamente prohibido** el uso de tipos de coma flotante binaria (`float` de Python o C) en cualquier punto del pipeline de conversión.

### Demostración del Riesgo de `float`:
En coma flotante IEEE-754:
```python
# PROHIBIDO
>>> 0.1 + 0.2
0.30000000000000004
>>> float(1000) * 0.0001
0.09999999999999999
```
En un inventario con 1,000,000 de unidades, esto provoca descuadres de stock físicos.

### Solución Estricta en `Decimal`:
```python
# OBLIGATORIO
>>> Decimal('0.1') + Decimal('0.2')
Decimal('0.3')
>>> Decimal('1000') * Decimal('0.0001')
Decimal('0.1000')
```

---

## 3. Salidas del Motor: `exact_result`, `rounded_result` y `residual`

Toda respuesta de conversión genera 3 valores clave:

1. **`exact_result`**: Resultado de multiplicar $Q \times F_{eff}$ manteniendo la escala completa de 18 decimales.
2. **`rounded_result`**: Valor ajustado a las necesidades operativas de la orden (ej. no se pueden pickear $2.333333$ cajas, se redondea a $2$ o $3$ según política).
3. **`residual`**: Diferencia no cubierta o remanente en la unidad de origen $Q_{orig} - \left( \frac{Q_{rounded}}{F_{eff}} \right)$, garantizando que nada de stock se pierda "en el aire".
