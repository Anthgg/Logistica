# 12 — Condiciones de Almacenamiento y Matriz Ambiental (`ProductStorageConditionModel`)

## 1. Definición del Perfil de Almacenamiento

Determinados productos imponen restricciones térmicas, higrométricas o de peligrosidad de estricto cumplimiento para evitar su degradación o riesgos ocupacionales (ej. medicamentos biológicos a $2^\circ\text{C}-8^\circ\text{C}$, químicos inflamables Hazmat o productos higroscópicos).

La **Fase 023** introduce la entidad `ProductStorageConditionModel` para definir formalmente los rangos ambientales permitidos y la severidad de las reglas de bloqueo en el almacén.

---

## 2. Esquema Relacional de `product_storage_conditions`

```sql
CREATE TYPE constraint_severity_enum AS ENUM (
    'HARD_BLOCK',    -- Bloqueo estricto. Impide almacenar el producto si la ubicación no cumple.
    'WARNING_ONLY'   -- Alerta / Advertencia operativa, pero permite forzar el almacenamiento.
);

CREATE TABLE product_storage_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    min_temperature_celsius NUMERIC(5, 2) NULL, -- Ej: -20.00
    max_temperature_celsius NUMERIC(5, 2) NULL, -- Ej: -15.00
    
    min_humidity_percentage NUMERIC(5, 2) NULL, -- Ej: 30.00 %
    max_humidity_percentage NUMERIC(5, 2) NULL, -- Ej: 65.00 %
    
    requires_refrigeration BOOLEAN NOT NULL DEFAULT FALSE,
    requires_freezing BOOLEAN NOT NULL DEFAULT FALSE,
    
    is_hazmat BOOLEAN NOT NULL DEFAULT FALSE,
    hazmat_class VARCHAR(20) NULL, -- Clases ONU: "3" (Flammables), "6.1" (Toxic), "8" (Corrosive)
    un_number VARCHAR(10) NULL,    -- Código UN de Naciones Unidas (Ej: "UN1203")
    
    is_fragile BOOLEAN NOT NULL DEFAULT FALSE,
    requires_darkness BOOLEAN NOT NULL DEFAULT FALSE,
    
    severity constraint_severity_enum NOT NULL DEFAULT 'HARD_BLOCK',

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_storage_condition_product UNIQUE (product_id),
    CONSTRAINT chk_temperature_range CHECK (
        (min_temperature_celsius IS NULL OR max_temperature_celsius IS NULL) 
        OR (max_temperature_celsius >= min_temperature_celsius)
    ),
    CONSTRAINT chk_humidity_range CHECK (
        (min_humidity_percentage IS NULL OR max_humidity_percentage IS NULL)
        OR (max_humidity_percentage >= min_humidity_percentage)
    )
);

CREATE INDEX idx_storage_conditions_product ON product_storage_conditions(product_id);
```

---

## 3. Modelo SQLAlchemy (`ProductStorageConditionModel`)

```python
import enum
from sqlalchemy import Column, String, Numeric, Boolean, Enum as SQLEnum, ForeignKey, UniqueConstraint, Index, CheckConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class ConstraintSeverity(str, enum.Enum):
    HARD_BLOCK = "HARD_BLOCK"
    WARNING_ONLY = "WARNING_ONLY"

class ProductStorageConditionModel(Base):
    __tablename__ = "product_storage_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    min_temperature_celsius = Column(Numeric(5, 2), nullable=True)
    max_temperature_celsius = Column(Numeric(5, 2), nullable=True)

    min_humidity_percentage = Column(Numeric(5, 2), nullable=True)
    max_humidity_percentage = Column(Numeric(5, 2), nullable=True)

    requires_refrigeration = Column(Boolean, nullable=False, default=False)
    requires_freezing = Column(Boolean, nullable=False, default=False)

    is_hazmat = Column(Boolean, nullable=False, default=False)
    hazmat_class = Column(String(20), nullable=True)
    un_number = Column(String(10), nullable=True)

    is_fragile = Column(Boolean, nullable=False, default=False)
    requires_darkness = Column(Boolean, nullable=False, default=False)

    severity = Column(SQLEnum(ConstraintSeverity), nullable=False, default=ConstraintSeverity.HARD_BLOCK)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("ProductModel", back_populates="storage_condition")

    __table_args__ = (
        UniqueConstraint("product_id", name="uq_storage_condition_product"),
        CheckConstraint(
            "(min_temperature_celsius IS NULL OR max_temperature_celsius IS NULL) OR (max_temperature_celsius >= min_temperature_celsius)",
            name="chk_temperature_range"
        ),
        CheckConstraint(
            "(min_humidity_percentage IS NULL OR max_humidity_percentage IS NULL) OR (max_humidity_percentage >= min_humidity_percentage)",
            name="chk_humidity_range"
        ),
        Index("idx_storage_conditions_product", "product_id"),
    )
```

---

## 4. Matriz de Clasificación Hazmat y Temperatura

| Condición | Campo | Ejemplo de Valor | Significado Logístico |
| :--- | :--- | :--- | :--- |
| **Congelación** | `requires_freezing` | `TRUE` ($-25^\circ\text{C}$ a $-18^\circ\text{C}$) | Solo puede ubicarse en cámaras de ultracongelación. |
| **Refrigeración** | `requires_refrigeration` | `TRUE` ($2^\circ\text{C}$ a $8^\circ\text{C}$) | Solo puede ubicarse en zonas con control térmico de frío. |
| **Hazmat Clase 3** | `hazmat_class` | `"3"` (Líquidos Inflamables) | Requiere almacén APQ / extintores de espuma / ventilación. |
| **Código UN** | `un_number` | `"UN1203"` (Gasolina) | Obligatorio en manifiestos de transporte peligrosos. |
| **Frágil** | `is_fragile` | `TRUE` | Prohibido ubicar en casilleros superiores sin barrera de retención. |

---

## 5. Severidad de Bloqueo (`HARD_BLOCK` vs `WARNING_ONLY`)

- `HARD_BLOCK`: Si la ubicación destino no cumple con los requisitos del producto (ej. ubicar un producto de congelación en un pasillo a temperatura ambiente), la transacción de asignación de ubicación en la Fase 044 (*Putaway*) fallará arrojando un error `422 Unprocessable Entity`.
- `WARNING_ONLY`: Emite una alerta auditada en `logistics_audit_events` pero permite al operador autorizar excepcionalmente la ubicación si cuenta con el permiso `logistics.override_storage_warning`.
