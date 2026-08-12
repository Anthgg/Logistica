# 06. Validador Sintáctico de RUC Peruano (Módulo 11)

## Alcance y Deslinde de Responsabilidad

El componente `PeruvianRucValidator` implementa la **validación sintáctica de formato y dígito verificador** para el Registro Único de Contribuyentes (RUC) expedido por la SUNAT en la República del Perú.

> [!IMPORTANT]
> **Deslinde de SUNAT (Phase Scope Boundaries):**
> La Fase 025 ejecuta estrictamente **validación sintáctica matemática offline** sin realizar llamadas HTTP externas. La consulta de estado tributario en tiempo real (Condición de Habido/No Habido, Estado Activo/Baja) y scraping/API oficial de SUNAT/RENIEC corresponde contractualmente a la **Fase 026 (Consulta Externa de Padrones)**.

---

## Reglas Sintácticas del RUC Peruano

1. **Longitud:** Exactamente **11 dígitos numéricos** (caracteres `0-9`).
2. **Prefijos Válidos de Entidad:**
   * `10`: Persona Natural con Negocio.
   * `15`: Persona Natural (Extranjero registrado).
   * `16`: Persona Natural (DNI especial).
   * `17`: Persona Natural (Fuerzas Armadas / Policiales).
   * `20`: Persona Jurídica (Empresas, Sociedades Anónimas, EIRL, Sociedades Civiles).
3. **Algoritmo Dígito Verificador (Módulo 11):**
   El 11º dígito del RUC corresponde al dígito de control generado mediante una ponderación sobre los primeros 10 dígitos.

---

## Algoritmo Módulo 11 (Pesos y Cálculo)

Los factores de ponderación aplicados secuencialmente a los primeros 10 dígitos son:
**Factores:** `[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]`

### Pasos del Algoritmo:
1. Multiplicar cada dígito del RUC ($d_1, d_2, \dots, d_{10}$) por su factor correspondiente ($w_1, w_2, \dots, w_{10}$).
2. Sumar todos los productos: $S = \sum_{i=1}^{10} (d_i \times w_i)$.
3. Calcular el residuo de la división entre 11: $R = S \pmod{11}$.
4. Restar el residuo a 11: $V = 11 - R$.
5. **Regla de ajuste:**
   * Si $V = 10 \implies \text{Dígito Verificador} = 0$.
   * Si $V = 11 \implies \text{Dígito Verificador} = 1$.
   * En cualquier otro caso $\implies \text{Dígito Verificador} = V$.
6. Comparar el dígito calculado con el 11º dígito ($d_{11}$) del RUC evaluado.

---

## Implementación en Python (`PeruvianRucValidator`)

```python
import re
from typing import Tuple, Optional

class RucValidationResult:
    def __init__(self, is_valid: bool, status_code: str, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.status_code = status_code # FORMAT_VALID, INVALID_LENGTH, INVALID_PREFIX, INVALID_CHECKSUM
        self.error_message = error_message

class PeruvianRucValidator:
    VALID_PREFIXES = {"10", "15", "16", "17", "20"}
    WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    @classmethod
    def validate(cls, ruc_string: str) -> RucValidationResult:
        if not ruc_string:
            return RucValidationResult(False, "INVALID_LENGTH", "El RUC no puede estar vacío.")
        
        # Limpieza de espacios en blanco
        cleaned_ruc = ruc_string.strip()

        # 1. Validar solo caracteres numéricos y longitud exactamente de 11
        if not re.match(r"^\d{11}$", cleaned_ruc):
            return RucValidationResult(
                False, 
                "INVALID_LENGTH", 
                f"El RUC debe contener exactamente 11 dígitos numéricos. Recibido: '{cleaned_ruc}'."
            )

        # 2. Validar prefijo permitido
        prefix = cleaned_ruc[:2]
        if prefix not in cls.VALID_PREFIXES:
            return RucValidationResult(
                False, 
                "INVALID_PREFIX", 
                f"El prefijo '{prefix}' no es válido para RUC peruano. Debe iniciar con {sorted(list(cls.VALID_PREFIXES))}."
            )

        # 3. Algoritmo Módulo 11 para dígito verificador
        digits = [int(ch) for ch in cleaned_ruc]
        expected_checksum = digits[10]

        total_sum = sum(digits[i] * cls.WEIGHTS[i] for i in range(10))
        remainder = total_sum % 11
        calculated_value = 11 - remainder

        if calculated_value == 10:
            calculated_checksum = 0
        elif calculated_value == 11:
            calculated_checksum = 1
        else:
            calculated_checksum = calculated_value

        if calculated_checksum != expected_checksum:
            return RucValidationResult(
                False, 
                "INVALID_CHECKSUM", 
                f"El dígito verificador es incorrecto. Esperado sintácticamente: {calculated_checksum}, recibido: {expected_checksum}."
            )

        return RucValidationResult(True, "FORMAT_VALID", None)
```

---

## Integración con `BusinessPartnerService`

Al procesar la creación o actualización de un socio con `tax_id_type == "RUC"` y `country_code == "PE"`, el servicio invoca obligatoriamente `PeruvianRucValidator.validate(tax_id_value)`:

```python
if partner_in.tax_id_type == "RUC" and partner_in.country_code == "PE":
    val_result = PeruvianRucValidator.validate(partner_in.tax_id_value)
    if not val_result.is_valid:
        raise InvalidTaxIdException(
            code=val_result.status_code, 
            message=val_result.error_message
        )
```
Si el resultado es invalido, se rechaza la solicitud retornando `HTTP 422 Unprocessable Entity` sin registrar el objeto en base de datos.
