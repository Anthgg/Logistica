# Servicio de Normalización de VIN (ISO 3779) y Enmascaramiento

## 1. Servicio `VehicleVinService`

El número de identificación vehicular (VIN - *Vehicle Identification Number*) es el estándar internacional estipulado en la norma **ISO 3779** para la identificación unívoca de unidades motrices a nivel mundial.

El servicio `VehicleVinService` (`app/services/logistics/vehicle_vin_service.py`) gestiona la validación estructural, canonización y enmascaramiento de seguridad de este atributo en `VehicleModel`.

---

## 2. Estructura y Validación ISO 3779

Un VIN válido bajo ISO 3779 consta de **17 caracteres alfanuméricos** divididos en 3 secciones principales:

```
+------------------+-----------------------+---------------------+
|   WMI (1-3)      |       VDS (4-9)       |      VIS (10-17)    |
+------------------+-----------------------+---------------------+
| World Manufacturer| Vehicle Descriptor   | Vehicle Identifier  |
| Identifier       | Section               | Section (Serial)    |
+------------------+-----------------------+---------------------+
```

### Reglas de Exclusión de Caracteres:
Bajo la especificación ISO 3779, las letras **`I` (i)**, **`O` (o)** y **`Q` (q)** están **estrictamente prohibidas** en cualquier posición del VIN para evitar confusiones visuales con los dígitos `1` y `0`.

```python
import re

class VehicleVinService:
    VIN_REGEX = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

    @classmethod
    def validate_and_normalize(cls, raw_vin: str | None) -> str | None:
        if not raw_vin:
            return None
            
        clean_vin = raw_vin.strip().upper()
        
        if len(clean_vin) != 17:
            raise ValueError(f"El VIN '{raw_vin}' debe tener exactamente 17 caracteres (longitud actual: {len(clean_vin)}).")
            
        if not cls.VIN_REGEX.match(clean_vin):
            raise ValueError(f"El VIN '{raw_vin}' contiene caracteres inválidos (I, O, Q no están permitidos por ISO 3779).")
            
        return clean_vin
```

---

## 3. Política de Privacidad y Enmascaramiento

Por motivos de seguridad, prevención de clonación vehicular y cumplimiento de políticas de protección de datos sensibles en reportes públicos o exportaciones no privilegiadas, el sistema provee una función de enmascaramiento del VIN.

### Estrategia de Enmascaramiento:
* Se conservan visibles los 3 primeros caracteres (**WMI** - Identificador de fabricante) y los últimos 4 caracteres del número de serie (**VIS**).
* Se reemplazan los 10 caracteres intermedios por asteriscos (`*`).

```python
@classmethod
def mask_vin(cls, vin: str | None) -> str | None:
    """
    Transforma '19VDE1F28GE012345' -> '19V**********2345'
    """
    if not vin or len(vin) != 17:
        return vin
    return f"{vin[:3]}**********{vin[-4:]}"
```

---

## 4. Unicidad y Búsqueda

El campo `normalized_vin` almacena el valor procesado por `validate_and_normalize`. 
* Si se proporciona un VIN, debe ser **único globalmente** en la tabla `logistics_vehicles` para evitar registros duplicados de unidades motrices entre organizaciones o filiales.
* En búsquedas por API, los parámetros de consulta admiten tanto el VIN completo como el VIN enmascarado o la búsqueda parcial por el segmento serial (VIS).
