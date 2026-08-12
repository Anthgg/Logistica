# 06 — Categorías de Licencia y Asignaciones (`DriverLicenseCategoryModel`)

## Maestro de Categorías MTC de Perú

El Ministerio de Transportes y Comunicaciones (MTC) define una jerarquía y alcance específico para cada categoría de licencia de conducir. La plataforma expone un maestro administrable `DriverLicenseCategoryModel` (`logistics_driver_license_categories`).

---

## Catálogo Estándar de Categorías MTC

| Categoría | Código | Descripción MTC | Vehículos Autorizados | Jerarquía |
|---|---|---|---|---|
| **A-I** | `A-I` | Particular / Automóviles | Coupé, Sedan, Station Wagon, SUV | 1 |
| **A-IIa** | `A-IIa` | Transporte de Pasajeros Menor | Taxis, Ambulancias, Moto taxis | 2 |
| **A-IIb** | `A-IIb` | Transporte Carga Liviana y Bus Menor | Microbuses (hasta 16 asientos), Camiones pequeños (hasta 12 Tn) | 3 |
| **A-IIIa** | `A-IIIa` | Transporte de Pasajeros Mayor | Omnibuses urbanos e interprovinciales articulados | 4 |
| **A-IIIb** | `A-IIIb` | Transporte de Carga Pesada | Camiones pesados, Chasis remolcables, Tráilers, Volquetes | 4 |
| **A-IIIc** | `A-IIIc` | Categoría Máxima Especial / Combinada | Autoriza la conducción de TODOS los vehículos de A-I, A-IIa, A-IIb, A-IIIa y A-IIIb | 5 |

---

## Esquema SQL de Categorías y Asignaciones

```sql
CREATE TABLE logistics_driver_license_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE, -- A-I, A-IIa, A-IIb, A-IIIa, A-IIIb, A-IIIc
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    hierarchy_level INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE logistics_driver_license_category_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID NOT NULL REFERENCES logistics_driver_licenses(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES logistics_driver_license_categories(id) ON DELETE CASCADE,
    
    assigned_at DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_license_category UNIQUE (license_id, category_id)
);

CREATE INDEX idx_license_category_assign ON logistics_driver_license_category_assignments(license_id, category_id);
```

---

## Atributos SQLAlchemy

```python
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class DriverLicenseCategoryModel(Base):
    __tablename__ = "logistics_driver_license_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    assignments = relationship("DriverLicenseCategoryAssignmentModel", back_populates="category")

class DriverLicenseCategoryAssignmentModel(Base):
    __tablename__ = "logistics_driver_license_category_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_driver_licenses.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_driver_license_categories.id", ondelete="CASCADE"), nullable=False)
    
    assigned_at: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    license = relationship("DriverLicenseModel", back_populates="category_assignments")
    category = relationship("DriverLicenseCategoryModel", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("license_id", "category_id", name="uq_license_category"),
    )
```

---

## Inclusión Hereditaria de Categorías (Regla A-IIIc)

La categoría **A-IIIc** cubre automáticamente por principio legal del MTC todas las categorías inferiores. Por tanto, el evaluador de compatibilidad verifica:
1. Si la licencia tiene asignada la categoría específica requerida para el vehículo (ej. `A-IIIb`).
2. O si la licencia tiene asignada la categoría jerárquica superior `A-IIIc`.
