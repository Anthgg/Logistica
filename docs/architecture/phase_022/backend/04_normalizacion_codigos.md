# 04. Normalización y Construcción Determinística de Códigos

## Servicio `WarehouseLocationCodeService`

El servicio `WarehouseLocationCodeService` gestiona la sanitización, validación, generación de correlativos y construcción jerárquica de los códigos mnemónicos de ubicaciones en el sistema logístico.

---

## Formato del Código Jerárquico (`full_code`)

El `full_code` es una cadena única por almacén que resulta de la concatenación jerárquica de los códigos individuales (`code`) desde el nodo raíz hasta el nodo actual, utilizando el separador guion `-`.

### Ejemplo de Composición Determinística

```
[Almacén: ALM01]
  └── [Zona: Z01]                 => code: "Z01" | full_code: "ALM01-Z01"
       └── [Pasillo: A03]          => code: "A03" | full_code: "ALM01-Z01-A03"
            └── [Rack: R02]        => code: "R02" | full_code: "ALM01-Z01-A03-R02"
                 └── [Nivel: N04]  => code: "N04" | full_code: "ALM01-Z01-A03-R02-N04"
                      └── [Bin: P06] => code: "P06" | full_code: "ALM01-Z01-A03-R02-N04-P06"
```

```python
# app/services/logistics/code_service.py

import re
from typing import List, Optional

class WarehouseLocationCodeService:
    CODE_REGEX = re.compile(r"^[A-Z0-9_\-]{1,32}$")
    SEPARATORS = ["-", "_", " "]

    @classmethod
    def sanitize_code(cls, raw_code: str) -> str:
        """Sanitiza y normaliza un código a ASCII Mayúsculas."""
        if not raw_code:
            raise ValueError("El código no puede estar vacío.")
        
        sanitized = raw_code.strip().upper()
        sanitized = re.sub(r"[\s_]+", "-", sanitized)
        
        if not cls.CODE_REGEX.match(sanitized):
            raise ValueError(
                f"Código inválido '{raw_code}'. Debe contener solo caracteres Alfanuméricos ASCII Mayúsculas, guiones o guiones bajos (1-32 caracteres)."
            )
        return sanitized

    @classmethod
    def build_full_code(cls, warehouse_code: str, parent_full_code: Optional[str], node_code: str) -> str:
        """Construye el full_code concatenando la jerarquía."""
        clean_node = cls.sanitize_code(node_code)
        if not parent_full_code:
            clean_wh = cls.sanitize_code(warehouse_code)
            return f"{clean_wh}-{clean_node}"
        return f"{parent_full_code}-{clean_node}"
    
    @classmethod
    def suggest_next_correlative(cls, existing_codes: List[str], prefix: str, padding: int = 2) -> str:
        """Sugiere el siguiente código correlativo disponible (Ej: Z01 -> Z02)."""
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        max_seq = 0
        for code in existing_codes:
            match = pattern.match(code)
            if match:
                seq = int(match.group(1))
                if seq > max_seq:
                    max_seq = seq
        next_seq = max_seq + 1
        return f"{prefix}{str(next_seq).zfill(padding)}"
```

---

## Reglas de Validación de Caracteres

| Regla | Especificación | Ejemplo Válido | Ejemplo Inválido |
| :--- | :--- | :--- | :--- |
| **Juego de Caracteres** | ASCII Alfanumérico Mayúsculas (`A-Z`, `0-9`), Guión (`-`) | `ZONA-01`, `RACK-A` | `Zona-01`, `RACK#1` |
| **Longitud `code`** | Entre 1 y 32 caracteres. | `P06`, `RECEPCION` | `CADENA_CON_MAS_DE_TREINTA_Y_DOS_CARACTERES` |
| **Longitud `full_code`**| Máximo 255 caracteres en total. | `ALM01-Z01-A03-R02` | Cadena concatenada > 255 chars |
| **Normalización** | Conversión automática de minúsculas y espacios a guiones | Input: `" pasillo 3 "` -> `"PASILLO-3"` | Preservación de espacios |

---

## Sugerencias Correlativas para UI/API

El servicio expone el helper `suggest_next_correlative` utilizado por los endpoints de la API (`GET /api/logistics/warehouses/{id}/locations/suggest-code`) para pre-poblar formularios en el cliente web React, evitando colisiones de duplicidad al crear elementos continuos.
