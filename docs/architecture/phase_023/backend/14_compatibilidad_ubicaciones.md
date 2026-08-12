# 14 — Evaluador Cualitativo de Compatibilidad Producto-Ubicación

## 1. Propósito del Evaluador de Compatibilidad

Una de las integraciones arquitectónicas centrales entre la **Fase 023 (Catálogo de Productos)** y la **Fase 022 (Modelado de Almacenes y Ubicaciones)** es la capacidad de verificar cualitativamente si una ubicación física determinada es apta para almacenar un producto específico.

El servicio `EvaluateProductLocationCompatibility` realiza el cruce en memoria/SQL de las restricciones ambientales, físicas y normativas del producto contra las capacidades y restricciones configuradas en el nodo `WarehouseLocationModel` de la Fase 022, **sin consultar saldos de inventario ni alterar tablas de stock**.

---

## 2. Diagrama de Flujo del Evaluador

```mermaid
graph TD
    P[ProductModel + StorageCondition + PhysicalProfile] --> ENGINE[EvaluateProductLocationCompatibility]
    LOC[WarehouseLocationModel (Fase 022)] --> ENGINE

    ENGINE --> C1{1. ¿Ubicación Activa y Bloqueada?}
    C1 -->|Sí| FAIL1[INCOMPATIBLE: Ubicación Inactiva o Bloqueada]
    C1 -->|No| C2{2. ¿Cadena de Frío / Refrigeración?}

    C2 -->|Requiere Frío y Ubicación No Refrigerada| FAIL2[INCOMPATIBLE: Violación Térmica Refrigeración]
    C2 -->|Cumple| C3{3. ¿Restricción Hazmat?}

    C3 -->|Es Hazmat y Ubicación No Hazmat| FAIL3[INCOMPATIBLE: Ubicación No Autorizada para Materiales Peligrosos]
    C3 -->|Cumple| C4{4. ¿Capacidad de Peso / Dimensiones?}

    C4 -->|Peso Bruto > Capacidad Máx Ubicación| FAIL4[INCOMPATIBLE: Supera Capacidad de Carga Máxima]
    C4 -->|Cumple| OK[COMPATIBLE: Asignación Autorizada]

    classDef pass fill:#15803d,stroke:#22c55e,color:#fff;
    classDef fail fill:#b91c1c,stroke:#ef4444,color:#fff;
    classDef engine fill:#1e293b,stroke:#a855f7,color:#fff;

    class OK pass;
    class FAIL1,FAIL2,FAIL3,FAIL4 fail;
    class ENGINE engine;
```

---

## 3. Algoritmo de Evaluación (`EvaluateProductLocationCompatibility`)

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import List

@dataclass
class CompatibilityResult:
    is_compatible: bool
    reasons: List[str]
    severity: str # "HARD_BLOCK" o "WARNING_ONLY"

class ProductLocationCompatibilityEvaluator:

    @classmethod
    def evaluate(cls, product: ProductModel, location: "WarehouseLocationModel") -> CompatibilityResult:
        reasons = []
        is_compatible = True
        severity = "HARD_BLOCK"

        # 1. Validar estado operativo de la ubicación (Fase 022)
        if not location.is_active or location.is_blocked:
            is_compatible = False
            reasons.append(f"La ubicación '{location.full_code}' está inactiva o bloqueada operativamente.")

        # 2. Validar Condiciones de Almacenamiento Térmicas y Ambientales
        storage = product.storage_condition
        if storage:
            severity = storage.severity
            
            # Refrigeración / Congelación
            if storage.requires_refrigeration and not getattr(location, 'has_refrigeration', False):
                is_compatible = False
                reasons.append("El producto requiere refrigeración y la ubicación no cuenta con control de temperatura.")
                
            if storage.requires_freezing and not getattr(location, 'has_freezing', False):
                is_compatible = False
                reasons.append("El producto requiere congelación y la ubicación no soporta rango sub-cero.")

            # Hazmat / Materiales Peligrosos
            if storage.is_hazmat and not getattr(location, 'is_hazmat_approved', False):
                is_compatible = False
                reasons.append(f"El producto es Hazmat (Clase {storage.hazmat_class}) y la ubicación no cuenta con certificación APQ.")

        # 3. Validar Compatibilidad de Dimensiones Físicas y Peso
        physical = product.physical_profile
        if physical:
            max_weight_capacity = getattr(location, 'max_weight_kg', None)
            if max_weight_capacity and max_weight_capacity > Decimal("0"):
                if physical.gross_weight_kg > max_weight_capacity:
                    is_compatible = False
                    reasons.append(
                        f"El peso bruto del producto ({physical.gross_weight_kg} kg) excede la capacidad máxima de la ubicación ({max_weight_capacity} kg)."
                    )

        return CompatibilityResult(
            is_compatible=is_compatible,
            reasons=reasons,
            severity=severity
        )
```

---

## 4. Endpoint REST de Evaluación Cualitativa

`POST /api/logistics/products/{id}/evaluate-location-compatibility`

### Payload de Solicitud:
```json
{
  "location_id": "8f3b2c1a-9401-4b11-a8e5-333333333333"
}
```

### Respuesta HTTP 200 (Caso Incompatible):
```json
{
  "product_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "location_id": "8f3b2c1a-9401-4b11-a8e5-333333333333",
  "location_code": "ZONA-FR-A-01-02",
  "is_compatible": false,
  "severity": "HARD_BLOCK",
  "reasons": [
    "El producto requiere congelación y la ubicación no soporta rango sub-cero."
  ]
}
```

---

## 5. Garantía de Independencia de Saldo

El evaluador cualitativo se enfoca únicamente en las **reglas de negocio estructurales**. No valida ni modifica:
- Cantidades en stock disponible.
- Reserva de espacio por ocupación actual (*Current Payload / Weight*).
- Tablas de movimientos de almacén.

Estas reglas de capacidad volumétrica dinámica se evalúan durante la **Fase 044 (Estrategias de Putaway y Ubicación de Inventario)**.
