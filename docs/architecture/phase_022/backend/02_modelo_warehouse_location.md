# 02. Modelo `WarehouseLocationModel` y Jerarquía de Ubicaciones

## Definición del Modelo SQLAlchemy

La entidad `WarehouseLocationModel` mapea la tabla `warehouse_locations`. Representa cada nodo de la jerarquía de almacenamiento físico y lógico dentro de un almacén.

```python
# app/models/logistics/warehouse_location.py

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime

class WarehouseLocationModel(Base):
    __tablename__ = "warehouse_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=True)

    # Identificación y Código
    code = Column(String(32), nullable=False)
    full_code = Column(String(255), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=True)
    public_ref = Column(String(64), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))

    # Clasificación y Jerarquía
    location_type = Column(String(32), nullable=False) # ZONE, AISLE, RACK, LEVEL, POSITION, DOCK, STAGING_AREA
    status = Column(String(32), nullable=False, default="ACTIVE") # ACTIVE, BLOCKED, MAINTENANCE, QUARANTINE_ONLY
    hierarchy_path = Column(String(1024), nullable=False) # ej: /<root_id>/<child_id>/<this_id>
    depth = Column(Integer, nullable=False, default=0)
    sequence_order = Column(Integer, nullable=False, default=0)

    # Flags Operativos
    is_pickable = Column(Boolean, nullable=False, default=True)
    is_receivable = Column(Boolean, nullable=False, default=True)
    is_returnable = Column(Boolean, nullable=False, default=True)
    is_counted = Column(Boolean, nullable=False, default=True)

    # Metadata y Fechas
    attributes = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    organization = relationship("OrganizationModel")
    warehouse = relationship("WarehouseModel", back_populates="locations")
    parent = relationship("WarehouseLocationModel", remote_side=[id], backref="children")
    capacity = relationship("WarehouseLocationCapacityModel", uselist=False, back_populates="location", cascade="all, delete-orphan")
    restrictions = relationship("WarehouseLocationRestrictionModel", back_populates="location", cascade="all, delete-orphan")
```

---

## Campos Clave de Estructura y Navegación

### 1. `hierarchy_path` (Ruta de Jerarquía Inmutabilizada)
* **Formato:** `/UUID_RAIZ/UUID_NIVEL1/UUID_NIVEL2/UUID_ACTUAL`
* **Utilidad:** Permite realizar consultas de subárboles completos con operadores SQL `LIKE '/<path>/%'` o regex de PostgreSQL `~ '^/<path>'`, logrando respuestas en tiempo constante $\mathcal{O}(1)$ con soporte de índice B-Tree sin necesidad de CTEs recursivos costosos.

### 2. `depth` (Profundidad del Nodo)
* **Valores:** Entero entre `0` (Nodo Raíz - Zona) y `9` (Nivel Máximo Permitido = 10 niveles en total: 0 a 9).
* **Regla de Consistencia:** `depth = parent.depth + 1` (para nodos no raíz).

### 3. `sequence_order` (Ordenación de Recorrido Logístico)
* **Propósito:** Determina el orden de visita durante secuencias de picking o conteos cíclicos de inventario.

---

## Tipos de Ubicación (`location_type`)

```mermaid
enumGraph
    ZONE["ZONE: Área o sector principal"]
    SUB_ZONE["SUB_ZONE: Sub-sector de almacenamiento"]
    AISLE["AISLE: Pasillo físico de tránsito"]
    RACK["RACK: Estante o estructura paletizada"]
    SHELF["SHELF: Mueble o anaquel multinivel"]
    LEVEL["LEVEL: Altura o bandeja dentro del rack"]
    POSITION["POSITION: Casillero o bin individual"]
    DOCK["DOCK: Muelle de carga / descarga"]
    STAGING["STAGING_AREA: Zona temporal de despacho"]
```

---

## Estados Operativos (`status`)

| Estado | Significado | Habilita Picking | Habilita Recepción |
| :--- | :--- | :---: | :---: |
| `ACTIVE` | Ubicación completamente operativa y disponible. | **SÍ** | **SÍ** |
| `BLOCKED` | Bloqueada temporalmente por auditoría o daño estructural. | **NO** | **NO** |
| `MAINTENANCE` | En mantenimiento preventivo o reparación física. | **NO** | **NO** |
| `QUARANTINE_ONLY` | Exclusiva para productos en cuarentena / control de calidad. | **NO** | **SÍ (Solo Cuarentena)** |

---

## Restricciones DDL e Índices B-Tree

```sql
-- Restricciones de Dominio y Unicidad
ALTER TABLE warehouse_locations ADD CONSTRAINT chk_location_depth CHECK (depth >= 0 AND depth <= 9);
ALTER TABLE warehouse_locations ADD CONSTRAINT uq_location_full_code UNIQUE (warehouse_id, full_code);
ALTER TABLE warehouse_locations ADD CONSTRAINT uq_location_public_ref UNIQUE (public_ref);

-- Índices de Rendimiento Jerárquico
CREATE INDEX idx_wh_loc_hierarchy_path ON warehouse_locations (hierarchy_path varchar_pattern_ops);
CREATE INDEX idx_wh_loc_parent_depth ON warehouse_locations (parent_id, depth);
CREATE INDEX idx_wh_loc_org_wh ON warehouse_locations (organization_id, warehouse_id, status);
```
