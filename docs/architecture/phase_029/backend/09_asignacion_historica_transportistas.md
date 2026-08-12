# 09 — Asignación Histórica de Transportistas (`DriverCarrierAssignmentModel`)

## Propósito y Vínculo con Socios Comerciales

Un conductor puede trabajar directamente para la empresa titular de la plataforma (conductor propio) o pertenecer a una empresa transportista externa contratada o subcontratada (tercero / `CARRIER`).

El modelo `DriverCarrierAssignmentModel` (`logistics_driver_carrier_assignments`) mantiene el **historial de vinculación auditado y temporalizado** entre los conductores y los socios comerciales de tipo Transportista (`BusinessPartner` con rol `CARRIER`).

---

## Esquema SQL de `logistics_driver_carrier_assignments`

```sql
CREATE TABLE logistics_driver_carrier_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    carrier_business_partner_id UUID NOT NULL REFERENCES logistics_business_partners(id) ON DELETE RESTRICT,
    
    relationship_type VARCHAR(30) NOT NULL DEFAULT 'SUBCONTRACTED', -- DIRECT_EMPLOYEE, INDEPENDENT_CONTRACTOR, SUBCONTRACTED
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    start_date DATE NOT NULL,
    end_date DATE NULL,
    
    contract_reference VARCHAR(100) NULL,
    notes TEXT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NULL REFERENCES sys_users(id),
    
    CONSTRAINT uq_active_driver_carrier UNIQUE (driver_id, carrier_business_partner_id, start_date)
);

CREATE INDEX idx_carrier_assign_driver ON logistics_driver_carrier_assignments(driver_id, is_active);
CREATE INDEX idx_carrier_assign_partner ON logistics_driver_carrier_assignments(carrier_business_partner_id, is_active);
```

---

## Atributos del Modelo SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class CarrierRelationshipType(str, Enum):
    DIRECT_EMPLOYEE = "DIRECT_EMPLOYEE"
    INDEPENDENT_CONTRACTOR = "INDEPENDENT_CONTRACTOR"
    SUBCONTRACTED = "SUBCONTRACTED"

class DriverCarrierAssignmentModel(Base):
    __tablename__ = "logistics_driver_carrier_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    carrier_business_partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_business_partners.id", ondelete="RESTRICT"), nullable=False)
    
    relationship_type: Mapped[CarrierRelationshipType] = mapped_column(String(30), default=CarrierRelationshipType.SUBCONTRACTED, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    contract_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True)

    driver = relationship("DriverModel", back_populates="carrier_assignments")
    # business_partner = relationship("BusinessPartnerModel") # Vinculación con socios comerciales
```

---

## Reglas de Negocio del Historial de Asignaciones

1. **Fecha de Inicio y Fin**: Al desvincular a un conductor de una empresa transportista, no se elimina la fila; se actualiza `is_active = FALSE` y se registra la `end_date = CURRENT_DATE`.
2. **Soporte Multitransportista**: Un conductor independiente puede tener asignaciones activas con más de un transportista si su contrato lo autoriza.
3. **Validación de Rol de Socio Comercial**: El servicio de asignación valida previamente que el `BusinessPartner` tenga asignado el rol `CARRIER` y esté en estado `ACTIVE`.
