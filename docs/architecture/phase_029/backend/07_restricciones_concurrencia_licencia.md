# 07 — Restricciones de Licencia de Conducir (`DriverLicenseRestrictionModel`)

## Definición y Tipos de Restricción

Las restricciones son anotaciones físicas impuestas por la autoridad de tránsito (MTC) en el reverso de la licencia de conducir. El modelo `DriverLicenseRestrictionModel` (`logistics_driver_license_restrictions`) registra y clasifica dichas restricciones evaluando su impacto en la asignación operativa.

---

## Clasificación de Restricciones y Severidad

| Código Restricción | Descripción MTC | Severidad | Impacto Operativo |
|---|---|---|---|
| `REST_CORRECTIVE_LENSES` | Uso obligatorio de lentes / corrección visual | `INFORMATIONAL` | Requiere verificación de portación de lentes por el conductor. No bloquea asignación. |
| `REST_HEARING_AID` | Uso obligatorio de audífonos para apoyo auditivo | `INFORMATIONAL` | Exige equipamiento auditivo. No bloquea si se cuenta con el dispositivo. |
| `REST_AUTOMATIC_TRANS` | Vehículo adaptado o con transmisión automática únicamente | `BLOCKING` | Bloquea asignación a vehículos con caja de cambios manual / mecánica. |
| `REST_DAYTIME_ONLY` | Restricción de conducción nocturna (sólo diurno) | `CONDITIONAL` | Bloquea asignación a viajes programados en horario nocturno (20:00 - 06:00). |
| `REST_SPECIAL_CONTROLS` | Mandos adaptados en el volante / palanca | `BLOCKING` | Bloquea asignación a flota convencional no adaptada. |

---

## Esquema SQL de `logistics_driver_license_restrictions`

```sql
CREATE TABLE logistics_driver_license_restrictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID NOT NULL REFERENCES logistics_driver_licenses(id) ON DELETE CASCADE,
    
    code VARCHAR(50) NOT NULL, -- REST_CORRECTIVE_LENSES, REST_AUTOMATIC_TRANS, etc.
    description VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFORMATIONAL', -- INFORMATIONAL, CONDITIONAL, BLOCKING
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_license_restrictions_license ON logistics_driver_license_restrictions(license_id);
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

class RestrictionSeverity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    CONDITIONAL = "CONDITIONAL"
    BLOCKING = "BLOCKING"

class DriverLicenseRestrictionModel(Base):
    __tablename__ = "logistics_driver_license_restrictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_driver_licenses.id", ondelete="CASCADE"), nullable=False)
    
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[RestrictionSeverity] = mapped_column(String(20), default=RestrictionSeverity.INFORMATIONAL, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    license = relationship("DriverLicenseModel", back_populates="restrictions")
```

---

## Lógica de Evaluación de Severidad

Cuando el motor `DriverOperationalEligibilityResolver` o `EvaluateDriverVehicleCompatibility` evalúa un conductor:
1. Si encuentra restricciones con `severity = 'BLOCKING'` inconciliables con el vehículo (ejemplo: restricción `REST_AUTOMATIC_TRANS` asignada a un camión mecánico), emite una objeción insubsanable y marca la compatibilidad como `INCOMPATIBLE`.
2. Si encuentra restricciones `CONDITIONAL`, valida las condiciones operativas de la ruta/viaje (ej. horario diurno/nocturno).
