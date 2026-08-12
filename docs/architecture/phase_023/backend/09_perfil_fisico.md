# 09 — Perfil Físico y Métricas Volumétricas (`ProductPhysicalProfileModel`)

## 1. Importancia del Perfil Físico en la Gestión Logística

El perfil físico de un producto define las características tridimensionales y de masa que determinan su ocupación espacial en las ubicaciones del almacén (Fase 022), el cálculo de capacidad de peso en estanterías (*Racks*), el volumen para consolidación de carga en transporte (TMS) y la tarificación volumétrica.

Para prevenir imprecisiones causadas por el punto flotante IEEE 754 de la coma flotante estándar, la **Fase 023** almacena todas las dimensiones y pesos utilizando el tipo de dato SQL `Numeric(14,4)` manipulado mediante objetos `Decimal` de Python.

---

## 2. Esquema Relacional de `product_physical_profiles`

```sql
CREATE TABLE product_physical_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    net_weight_kg NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    gross_weight_kg NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    
    length_cm NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    width_cm NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    height_cm NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    
    calculated_volume_m3 NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    override_volume_m3 NUMERIC(14, 4) NULL, -- Volumen reportado si difiere de la geometría pura
    
    is_stackable BOOLEAN NOT NULL DEFAULT TRUE,
    max_stacking_layers INTEGER NULL, -- Límite de apilamiento en altura
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_physical_profile_product UNIQUE (product_id),
    CONSTRAINT chk_net_gross_weight CHECK (gross_weight_kg >= net_weight_kg),
    CONSTRAINT chk_positive_dimensions CHECK (
        length_cm >= 0 AND width_cm >= 0 AND height_cm >= 0
    )
);

CREATE INDEX idx_physical_profiles_product ON product_physical_profiles(product_id);
```

---

## 3. Motor de Cálculo Volumétrico (`ProductVolumeCalculator`)

El cálculo del volumen en metros cúbicos ($m^3$) se computa automáticamente a partir de las dimensiones en centímetros ($cm$):

$$\text{Volume } (m^3) = \frac{\text{length\_cm} \times \text{width\_cm} \times \text{height\_cm}}{1,000,000}$$

```python
from decimal import Decimal, ROUND_HALF_UP

class ProductVolumeCalculator:
    CUBIC_CENTIMETERS_PER_CUBIC_METER = Decimal("1000000.0000")

    @classmethod
    def calculate_volume_m3(cls, length_cm: Decimal, width_cm: Decimal, height_cm: Decimal) -> Decimal:
        """
        Calcula el volumen geométrico en metros cúbicos con precisión de 4 decimales.
        """
        if length_cm < Decimal("0") or width_cm < Decimal("0") or height_cm < Decimal("0"):
            raise ValueError("Las dimensiones físicas no pueden ser negativas.")
            
        raw_volume = (length_cm * width_cm * height_cm) / cls.CUBIC_CENTIMETERS_PER_CUBIC_METER
        return raw_volume.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def resolve_effective_volume_m3(cls, calculated_vol: Decimal, override_vol: Decimal | None) -> Decimal:
        """
        Retorna override_volume_m3 si está configurado; de lo contrario, el volumen geométrico calculado.
        """
        if override_vol is not None and override_vol > Decimal("0"):
            return override_vol.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return calculated_vol
```

---

## 4. Modelo SQLAlchemy (`ProductPhysicalProfileModel`)

```python
from sqlalchemy import Column, Numeric, Boolean, Integer, ForeignKey, UniqueConstraint, Index, CheckConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class ProductPhysicalProfileModel(Base):
    __tablename__ = "product_physical_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    net_weight_kg = Column(Numeric(14, 4), nullable=False, default=0.0000)
    gross_weight_kg = Column(Numeric(14, 4), nullable=False, default=0.0000)

    length_cm = Column(Numeric(14, 4), nullable=False, default=0.0000)
    width_cm = Column(Numeric(14, 4), nullable=False, default=0.0000)
    height_cm = Column(Numeric(14, 4), nullable=False, default=0.0000)

    calculated_volume_m3 = Column(Numeric(14, 4), nullable=False, default=0.0000)
    override_volume_m3 = Column(Numeric(14, 4), nullable=True)

    is_stackable = Column(Boolean, nullable=False, default=True)
    max_stacking_layers = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("ProductModel", back_populates="physical_profile")

    __table_args__ = (
        UniqueConstraint("product_id", name="uq_physical_profile_product"),
        CheckConstraint("gross_weight_kg >= net_weight_kg", name="chk_net_gross_weight"),
        CheckConstraint("length_cm >= 0 AND width_cm >= 0 AND height_cm >= 0", name="chk_positive_dimensions"),
        Index("idx_physical_profiles_product", "product_id"),
    )
```

---

## 5. Validaciones de Negocio del Perfil Físico

1. **Invariante Peso Bruto vs Neto:** `gross_weight_kg` no puede ser menor que `net_weight_kg`. Intentar guardar un peso bruto menor lanza una excepción de validación y falla el Check Constraint de DB.
2. **Apilamiento:** Si `is_stackable` es `FALSE`, `max_stacking_layers` debe ser forzado automáticamente a `1`.
3. **Trigger de Actualización de Volumen:** Toda modificación de `length_cm`, `width_cm` o `height_cm` dispara la recalculación automática de `calculated_volume_m3` previo a la persistencia en DB.
