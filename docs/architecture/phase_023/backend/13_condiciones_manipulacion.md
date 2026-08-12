# 13 — Condiciones de Manipulación y Seguridad Operativa (`ProductHandlingConditionModel`)

## 1. Definición del Perfil de Manipulación y EPP

Además del almacenamiento térmico o espacial, los productos en almacén imponen requerimientos ergonómicos, de manipulación segura y de Equipos de Protección Personal (EPP) para proteger la integridad física de los operarios de montacargas, pickers y embaladores.

La **Fase 023** incluye la entidad `ProductHandlingConditionModel` para explicitar las reglas de manipulación segura durante las tareas de recepción, almacenamiento, picking y despacho.

---

## 2. Esquema Relacional de `product_handling_conditions`

```sql
CREATE TABLE product_handling_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    requires_two_persons BOOLEAN NOT NULL DEFAULT FALSE, -- Exige 2 operarios por peso/volumen
    requires_forklift BOOLEAN NOT NULL DEFAULT FALSE,   -- Requiere montacargas / apilador mecánico
    
    orientation_instruction VARCHAR(50) NULL, -- Ej: "THIS_SIDE_UP", "DO_NOT_TILT", "KEEP_VERTICAL"
    max_tilting_degrees NUMERIC(5, 2) NULL,    -- Grados máximos de inclinación permitidos (Ej: 15.00)
    
    required_ppe TEXT[] NULL, -- Array de EPPs: ARRAY['GLOVES', 'HELMET', 'SAFETY_SHOES', 'RESPIRATOR']
    
    safety_notes TEXT NULL,   -- Instrucciones especiales de seguridad en Hoja MSDS
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_handling_condition_product UNIQUE (product_id)
);

CREATE INDEX idx_handling_conditions_product ON product_handling_conditions(product_id);
```

---

## 3. Modelo SQLAlchemy (`ProductHandlingConditionModel`)

```python
from sqlalchemy import Column, String, Text, Boolean, Numeric, ForeignKey, UniqueConstraint, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class ProductHandlingConditionModel(Base):
    __tablename__ = "product_handling_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    requires_two_persons = Column(Boolean, nullable=False, default=False)
    requires_forklift = Column(Boolean, nullable=False, default=False)

    orientation_instruction = Column(String(50), nullable=True)
    max_tilting_degrees = Column(Numeric(5, 2), nullable=True)

    required_ppe = Column(ARRAY(String), nullable=True)

    safety_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("ProductModel", back_populates="handling_condition")

    __table_args__ = (
        UniqueConstraint("product_id", name="uq_handling_condition_product"),
        Index("idx_handling_conditions_product", "product_id"),
    )
```

---

## 4. Clasificación de Equipos de Protección Personal (EPP)

El campo `required_ppe` almacena un arreglo de códigos estandarizados de EPP:

- `GLOVES`: Guantes de protección anticorte o dieléctricos.
- `HELMET`: Casco de seguridad industrial para trabajo en altura.
- `SAFETY_SHOES`: Calzado de seguridad con puntera de acero o composite.
- `RESPIRATOR`: Respirador autónomo o con filtro de partículas para Químicos/Polvos.
- `EYE_PROTECTION`: Gafas de seguridad o pantalla facial panorámica.
- `EAR_PROTECTION`: Protectores auditivos para zonas de alto ruido.

---

## 5. Integración con Tareas Operativas en RF/Handhelds

Cuando la plataforma genera una orden de picking o traslado interno (Fases 041-044) para un producto que posee `requires_two_persons = TRUE` o `required_ppe` configurado:

1. **Alerta en Terminal RF:** La aplicación móvil/handheld del operario despliega una pantalla emergente con aviso de seguridad en color de alta visibilidad (naranja/rojo).
2. **Confirmación Obligatoria:** El operario debe presionar la casilla *"Confirmo uso de EPP requerido"* antes de poder escanear la ubicación o el código de barras del producto.
3. **Asignación de Tareas:** Si `requires_two_persons = TRUE`, la tarea de picking solo puede ser aceptada si dos operarios registran su sesión activa en el mismo lote de trabajo.
