# 05 — Licencias de Conducir (`DriverLicenseModel`)

## Definición y Atributos de la Licencia

El modelo `DriverLicenseModel` (`logistics_driver_licenses`) gestiona las licencias de conducir emitidas por autoridades de transporte (ej. Ministerio de Transportes y Comunicaciones - MTC de Perú u organismos internacionales equivalentes).

---

## Esquema SQL de `logistics_driver_licenses`

```sql
CREATE TABLE logistics_driver_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    license_number VARCHAR(50) NOT NULL,
    normalized_license_number VARCHAR(50) NOT NULL,
    masked_license_number VARCHAR(50) NOT NULL,
    
    issuing_authority VARCHAR(100) NOT NULL DEFAULT 'MTC',
    issuing_country VARCHAR(3) NOT NULL DEFAULT 'PER',
    
    issued_at DATE NOT NULL,
    expires_at DATE NOT NULL,
    
    status VARCHAR(30) NOT NULL DEFAULT 'VALID', -- VALID, EXPIRED, SUSPENDED, REVOKED
    accumulated_points INT NOT NULL DEFAULT 0,
    
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_driver_license_num UNIQUE (normalized_license_number)
);

CREATE INDEX idx_license_normalized ON logistics_driver_licenses(normalized_license_number);
CREATE INDEX idx_license_expires_at ON logistics_driver_licenses(expires_at);
CREATE INDEX idx_license_status ON logistics_driver_licenses(status);
```

---

## Atributos del Modelo SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class LicenseStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"

class DriverLicenseModel(Base):
    __tablename__ = "logistics_driver_licenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    masked_license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    issuing_authority: Mapped[str] = mapped_column(String(100), default="MTC", nullable=False)
    issuing_country: Mapped[str] = mapped_column(String(3), default="PER", nullable=False)
    
    issued_at: Mapped[date] = mapped_column(Date, nullable=False)
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)
    
    status: Mapped[LicenseStatus] = mapped_column(String(30), default=LicenseStatus.VALID, nullable=False)
    accumulated_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="licenses")
    category_assignments = relationship("DriverLicenseCategoryAssignmentModel", back_populates="license", cascade="all, delete-orphan")
    restrictions = relationship("DriverLicenseRestrictionModel", back_populates="license", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("normalized_license_number", name="uq_driver_license_num"),
    )
```

---

## Enmascaramiento y Reglas de Negocio de Licencias

### Algoritmo de Enmascaramiento (`****5678`):
En Perú, la licencia de conducir habitualmente coincide con el número de DNI precedido o no por una letra (ej. `Q72849153` o `72849153`).
- Se conservan los últimos 4 dígitos visibles y se enmascara todo el resto con asteriscos (`****5678`).

### Reglas de Vigencia y Puntos MTC:
1. **Verificación de Fecha de Vencimiento**: Si `expires_at < current_date`, el estado se actualiza automáticamente a `EXPIRED`.
2. **Histórico de Puntos MTC**: Si `accumulated_points >= 100` (límite MTC de papeletas de tránsito), el estado de la licencia se marca como `SUSPENDED` por acumulación de puntos.
3. **Primary License**: Cada conductor sólo puede tener una licencia marcada como `is_primary = TRUE` de forma simultánea.
