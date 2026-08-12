# 04 — Especificación de Codificación Atómica (`PurchaseOrderCode`)

---

## 1. Patrón y Formato de Código Único de OC

Para garantizar la identificación unívoca, legibilidad comercial e inmutabilidad en la trazabilidad logística, la Fase 034 implementa el patrón de código estructurado de Orden de Compra:

$$\text{OC-}\{SITE\}-\{YEAR\}-\{CORRELATOR:06d\}$$

### Componentes de la Estructura:
* **Prefijo Fijo**: `OC` (Órden de Compra).
* **Identificador de Sede/Planta (`SITE`)**: Código ASCII de 3 a 5 caracteres en mayúsculas que representa la sede u organización emisora (e.g., `LIM` para Lima, `ARE` para Arequipa).
* **Año de Emisión (`YEAR`)**: Año fiscal de cuatro dígitos en formato UTC (`YYYY`, e.g., `2026`).
* **Correlativo Secuencial (`CORRELATOR:06d`)**: Número correlativo incremental con rellenado de ceros a la izquierda a 6 dígitos (e.g., `000001`, `000042`).

---

## 2. Value Object `PurchaseOrderCode`

El código de la Orden de Compra está representado por el Value Object inmutable `PurchaseOrderCode`:

```python
import re
from dataclasses import dataclass

PO_CODE_REGEX = re.compile(r"^OC-[A-Z0-9]{2,10}-\d{4}-\d{6}$")

@dataclass(frozen=True)
class PurchaseOrderCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("PurchaseOrderCode must be a string")
        
        normalized = self.value.strip().upper()
        object.__setattr__(self, "value", normalized)

        if not PO_CODE_REGEX.match(self.value):
            raise ValueError(
                f"Invalid Purchase Order code format: '{self.value}'. "
                "Expected format: 'OC-{SITE}-{YEAR}-{CORRELATION_ID:06d}' (e.g. 'OC-LIM-2026-000001')"
            )

    @classmethod
    def format(cls, site_code: str, year: int, correlator: int) -> PurchaseOrderCode:
        clean_site = site_code.strip().upper()
        formatted = f"OC-{clean_site}-{year:04d}-{correlator:06d}"
        return cls(formatted)

    def __str__(self) -> str:
        return self.value
```

---

## 3. Garantía de Generación Atómica y Concurrencia

Para prevenir duplicados o condiciones de carrera (Race Conditions) en entornos altamente concurrentes, la generación de correlativos utiliza secuencias PostgreSQL aisladas o bloqueos de fila explícitos (`SELECT FOR UPDATE`) por combinación de (Organización, Sede, Año).

### Mecanismo de Generación en Repositorio:

```sql
-- Estrategia de bloqueo atómico de correlativo anual por sede
SELECT current_correlator 
FROM po_site_correlators 
WHERE organization_id = :org_id 
  AND site_code = :site_code 
  AND year = :year 
FOR UPDATE;

UPDATE po_site_correlators 
SET current_correlator = current_correlator + 1 
WHERE organization_id = :org_id 
  AND site_code = :site_code 
  AND year = :year;
```

### Reglas de Inmutabilidad:
1. Una vez asignado el `PurchaseOrderCode` durante la transición de `DRAFT` a `PENDING_APPROVAL`, el código **nunca cambia**, incluso si la orden es rechazada, devuelta o cancelada.
2. Las revisiones posteriores mantienen el mismo `PurchaseOrderCode` principal y únicamente incrementan el número de versión interna (`revision_number`).
