# 06. Capacidades Configuradas de Ubicaciones

## Modelo `WarehouseLocationCapacityModel`

El modelo `WarehouseLocationCapacityModel` mapea la tabla `warehouse_location_capacities`. Define los parámetros y límites físicos máximos asignables a una ubicación específica.

> [!IMPORTANT]
> **Desacoplamiento Estricto:** La Fase 022 actúa como capa de **configuración de la infraestructura técnica**. Este modelo **no calcula ni almacena saldos de inventario en tiempo real, ocupación ni stock actual**. Dichos saldos, movimientos y cálculos dinámicos de volumen disponible corresponden a las futuras fases de inventario y saldos (Fases 041-046).

---

## Estructura DDL SQLAlchemy

```python
# app/models/logistics/warehouse_location_capacity.py

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class WarehouseLocationCapacityModel(Base):
    __tablename__ = "warehouse_location_capacities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Límites Físicos y Dimensiones
    max_weight_kg = Column(Numeric(12, 2), nullable=True)
    max_volume_cubic_meters = Column(Numeric(12, 4), nullable=True)
    usable_height_meters = Column(Numeric(8, 2), nullable=True)
    usable_width_meters = Column(Numeric(8, 2), nullable=True)
    usable_depth_meters = Column(Numeric(8, 2), nullable=True)
    
    # Unidades de Empaque Máximas
    max_pallets = Column(Integer, nullable=True)
    max_boxes = Column(Integer, nullable=True)
    max_units = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = relationship("WarehouseLocationModel", back_populates="capacity")
```

---

## Atributos de Configuración de Capacidad

| Campo | Tipo de Dato | Unidad de Medida | Descripción Técnica |
| :--- | :--- | :---: | :--- |
| `max_weight_kg` | `NUMERIC(12, 2)` | Kilogramos ($kg$) | Capacidad portante máxima de carga por resistencia de estructura. |
| `max_volume_cubic_meters` | `NUMERIC(12, 4)` | $m^3$ | Volumen geométrico útil de almacenamiento. |
| `usable_height_meters` | `NUMERIC(8, 2)` | Metros ($m$) | Altura despejada desde la base hasta la estructura superior. |
| `usable_width_meters` | `NUMERIC(8, 2)` | Metros ($m$) | Ancho frontal aprovechable. |
| `usable_depth_meters` | `NUMERIC(8, 2)` | Metros ($m$) | Profundidad del casillero. |
| `max_pallets` | `INTEGER` | Pallets estándar | Límite máximo de posicionado de estibas/pallets. |
| `max_boxes` | `INTEGER` | Cajas máster | Límite volumétrico sugerido en empaques terciarios. |
| `max_units` | `INTEGER` | Unidades | Límite de unidades sueltas para ubicaciones de picking. |

---

## Restricciones DDL e Integridad

```sql
ALTER TABLE warehouse_location_capacities 
    ADD CONSTRAINT chk_cap_weight CHECK (max_weight_kg IS NULL OR max_weight_kg >= 0),
    ADD CONSTRAINT chk_cap_volume CHECK (max_volume_cubic_meters IS NULL OR max_volume_cubic_meters >= 0),
    ADD CONSTRAINT chk_cap_pallets CHECK (max_pallets IS NULL OR max_pallets >= 0),
    ADD CONSTRAINT chk_cap_boxes CHECK (max_boxes IS NULL OR max_boxes >= 0),
    ADD CONSTRAINT chk_cap_units CHECK (max_units IS NULL OR max_units >= 0);
```

---

## Integración con Algoritmos Futuros

Las futuras fases (ej. Algoritmos de Putaway en Fase 044) utilizarán estos datos configurados para comparar `capacidad_maxima - peso_o_volumen_ocupado` y determinar automáticamente si la ubicación es apta para recibir una orden de almacenamiento.
