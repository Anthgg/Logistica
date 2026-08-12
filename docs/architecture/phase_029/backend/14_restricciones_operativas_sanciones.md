# 14 — Restricciones Operativas y Sanciones (`DriverOperationalRestrictionModel`)

## Propósito y Gestión de Sanciones Administrativas

El modelo `DriverOperationalRestrictionModel` (`logistics_driver_operational_restrictions`) permite aplicar **bloqueos administrativos, sanciones disciplinarias, inhabilitaciones temporales o definitivas** dictadas por la empresa o autoridades reguladoras a un conductor.

---

## Esquema SQL de `logistics_driver_operational_restrictions`

```sql
CREATE TABLE logistics_driver_operational_restrictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    restriction_type VARCHAR(40) NOT NULL, -- ADMINISTRATIVE_LOCK, DISCIPLINARY_SANCTION, ALCOHOL_TEST_FAILURE, SAFETY_VIOLATION, MEDICAL_LEAVE
    severity VARCHAR(20) NOT NULL DEFAULT 'TEMPORARY_SUSPENSION', -- WARNING, TEMPORARY_SUSPENSION, PERMANENT_BLOCK
    
    reason TEXT NOT NULL,
    start_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMPTZ NULL, -- NULL indica inhabilitación permanente o indefinida
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    issued_by UUID NOT NULL REFERENCES sys_users(id),
    revoked_by UUID NULL REFERENCES sys_users(id),
    revocation_reason TEXT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_op_restriction_driver ON logistics_driver_operational_restrictions(driver_id, is_active);
```

---

## Atributos SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class OperationalRestrictionType(str, Enum):
    ADMINISTRATIVE_LOCK = "ADMINISTRATIVE_LOCK"
    DISCIPLINARY_SANCTION = "DISCIPLINARY_SANCTION"
    ALCOHOL_TEST_FAILURE = "ALCOHOL_TEST_FAILURE"
    SAFETY_VIOLATION = "SAFETY_VIOLATION"
    MEDICAL_LEAVE = "MEDICAL_LEAVE"

class OperationalRestrictionSeverity(str, Enum):
    WARNING = "WARNING"
    TEMPORARY_SUSPENSION = "TEMPORARY_SUSPENSION"
    PERMANENT_BLOCK = "PERMANENT_BLOCK"

class DriverOperationalRestrictionModel(Base):
    __tablename__ = "logistics_driver_operational_restrictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    restriction_type: Mapped[OperationalRestrictionType] = mapped_column(String(40), nullable=False)
    severity: Mapped[OperationalRestrictionSeverity] = mapped_column(String(20), default=OperationalRestrictionSeverity.TEMPORARY_SUSPENSION, nullable=False)
    
    reason: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    issued_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=False)
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="operational_restrictions")
```

---

## Impacto Inmediato en la Elegibilidad Operativa

1. **Suspensión Automática**: Toda restricción activa con severidad `TEMPORARY_SUSPENSION` o `PERMANENT_BLOCK` cambia de forma síncrona el `eligibility_status` del conductor a `INELIGIBLE`.
2. **Revocación Auditada**: Una restricción activa solo puede ser desestimada/revocada por un usuario autorizado que posea el permiso `logistics.drivers.restrictions.revoke`, exigiendo registrar el motivo de revocación y generando un evento de auditoría.
