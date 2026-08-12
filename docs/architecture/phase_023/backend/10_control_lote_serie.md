# 10 — Políticas de Control de Lote y Serie (`ProductTrackingPolicyModel`)

## 1. Definición de Políticas de Trazabilidad Logística

No todos los productos se gestionan al mismo nivel de detalle en el almacén. Mientras que los materiales a granel se gestionan por cantidad simple, los productos farmacéuticos o perecederos requieren seguimiento por **Número de Lote (`LOT`)**, y los equipos electrónicos de alto valor requieren identificación por **Número de Serie (`SERIAL`)** único por pieza.

La **Fase 023** define la configuración cualitativa de trazabilidad del producto a través del modelo `ProductTrackingPolicyModel`, marcando explícitamente la creación y movimiento de lotes y series reales con la etiqueta **`PENDING_PHASE_046`**.

---

## 2. Esquema Relacional de `product_tracking_policies`

```sql
CREATE TYPE tracking_mode_enum AS ENUM (
    'NONE',           -- Sin seguimiento (Inventario por conteo general)
    'LOT',            -- Seguimiento por Número de Lote
    'SERIAL',         -- Seguimiento por Número de Serie individual
    'LOT_AND_SERIAL'  -- Requiere ambos (Lote y Serie)
);

CREATE TABLE product_tracking_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    tracking_mode tracking_mode_enum NOT NULL DEFAULT 'NONE',
    
    requires_serial_on_receipt BOOLEAN NOT NULL DEFAULT FALSE,
    requires_serial_on_dispatch BOOLEAN NOT NULL DEFAULT FALSE,
    
    lot_number_mask VARCHAR(50) NULL, -- Regex / Máscara de validación de lote (Ej: "LOT-[0-9]{6}")
    serial_number_mask VARCHAR(50) NULL, -- Regex / Máscara de serie (Ej: "SN-[A-Z0-9]{10}")
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_tracking_policy_product UNIQUE (product_id)
);

CREATE INDEX idx_tracking_policies_product ON product_tracking_policies(product_id);
```

---

## 3. Modelo SQLAlchemy (`ProductTrackingPolicyModel`)

```python
import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey, UniqueConstraint, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class TrackingMode(str, enum.Enum):
    NONE = "NONE"
    LOT = "LOT"
    SERIAL = "SERIAL"
    LOT_AND_SERIAL = "LOT_AND_SERIAL"

class ProductTrackingPolicyModel(Base):
    __tablename__ = "product_tracking_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    tracking_mode = Column(SQLEnum(TrackingMode), nullable=False, default=TrackingMode.NONE)

    requires_serial_on_receipt = Column(Boolean, nullable=False, default=False)
    requires_serial_on_dispatch = Column(Boolean, nullable=False, default=False)

    lot_number_mask = Column(String(50), nullable=True)
    serial_number_mask = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("ProductModel", back_populates="tracking_policy")

    __table_args__ = (
        UniqueConstraint("product_id", name="uq_tracking_policy_product"),
        Index("idx_tracking_policies_product", "product_id"),
    )
```

---

## 4. Desacoplamiento de Lotes y Series Reales (`PENDING_PHASE_046`)

> [!NOTE]
> **REGLA DE DESACOPLAMIENTO DE LA FASE 023:**
> La Fase 023 **NO CREA** instancias de números de lote en inventario ni registros físicos de números de serie. Únicamente configura la **política del maestro de productos**.
>
> La gestión operativa de tablas como `inventory_lots`, `inventory_serials`, asignación de lotes en recepción (*GRN*) y escaneo de números de serie en picking/packing está explícitamente pospuesta y etiquetada como **`PENDING_PHASE_046`**.

---

## 5. Matriz de Combinaciones de Política

| `tracking_mode` | `requires_serial_on_receipt` | `requires_serial_on_dispatch` | Regla Operativa en Recepción/Picking (Fase 046) |
| :--- | :--- | :--- | :--- |
| `NONE` | `FALSE` | `FALSE` | Solo se valida la cantidad de unidades (`base_unit_code`). |
| `LOT` | `FALSE` | `FALSE` | Se exige ingresar o seleccionar un `lot_number` válido. |
| `SERIAL` | `TRUE` | `TRUE` | Se exige escanear cada número de serie individual tanto al ingresar como al despachar. |
| `SERIAL` | `FALSE` | `TRUE` | La serie se captura únicamente al momento del empaque y despacho (*Pick & Pack*). |
| `LOT_AND_SERIAL` | `TRUE` | `TRUE` | Se exige capturar tanto el lote como las series asociadas individualmente. |
