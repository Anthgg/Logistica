# 13 — Matriz de Requisitos Documentales (`DriverDocumentRequirementModel`)

## Definición y Utilidad de la Matriz de Requisitos

No todas las operaciones logísticas exigen el mismo nivel de documentación. Una ruta urbana de paquetería requiere DNI y Licencia A-I, mientras que una ruta minera o de transporte de combustibles exige adicionales como Hazmat, Manejo Defensivo, Examen Médico Ocupacional y SCTR.

El modelo `DriverDocumentRequirementModel` (`logistics_driver_document_requirements`) parametriza las reglas de exigencia documental configurables por alcance operativo.

---

## Esquema SQL de `logistics_driver_document_requirements`

```sql
CREATE TABLE logistics_driver_document_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES sys_organizations(id) ON DELETE CASCADE,
    
    operational_scope VARCHAR(50) NOT NULL, -- URBAN_GENERAL, INTERPROVINCIAL_CARGO, HAZMAT_HAZARDOUS, MINING_SITE
    document_type_required VARCHAR(50) NOT NULL, -- DNI, LICENSE, DEFENSIVE_DRIVING_CERTIFICATE, HAZMAT_CERTIFICATE, MEDICAL_FITNESS_CERTIFICATE, SCTR_INSURANCE
    
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    max_validity_days INT NULL, -- Días de validez máxima requeridos
    warning_buffer_days INT NOT NULL DEFAULT 30, -- Días previos para alerta preventiva de vencimiento
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_org_scope_doc_req UNIQUE (organization_id, operational_scope, document_type_required)
);

CREATE INDEX idx_doc_req_org_scope ON logistics_driver_document_requirements(organization_id, operational_scope);
```

---

## Atributos SQLAlchemy

```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class DriverDocumentRequirementModel(Base):
    __tablename__ = "logistics_driver_document_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_organizations.id", ondelete="CASCADE"), nullable=False)
    
    operational_scope: Mapped[str] = mapped_column(String(50), nullable=False)
    document_type_required: Mapped[str] = mapped_column(String(50), nullable=False)
    
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warning_buffer_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "operational_scope", "document_type_required", name="uq_org_scope_doc_req"),
    )
```

---

## Ejemplo de Configuración de Matriz por Alcance Operativo

| Operational Scope | Document Type Required | Mandatory? | Buffer Días |
|---|---|---|---|
| `URBAN_GENERAL` | `DNI` | Sí | 30 días |
| `URBAN_GENERAL` | `LICENSE` | Sí | 30 días |
| `HAZMAT_HAZARDOUS` | `DNI` | Sí | 30 días |
| `HAZMAT_HAZARDOUS` | `LICENSE` | Sí | 30 días |
| `HAZMAT_HAZARDOUS` | `HAZMAT_CERTIFICATE` | Sí | 45 días |
| `HAZMAT_HAZARDOUS` | `DEFENSIVE_DRIVING_CERTIFICATE` | Sí | 30 días |
| `HAZMAT_HAZARDOUS` | `MEDICAL_FITNESS_CERTIFICATE` | Sí | 30 días |
| `MINING_SITE` | `SCTR_INSURANCE` | Sí | 15 días |
