# 12 — Documentos Adicionales y Capacitación (`DriverDocumentModel`)

## Propósito y Tipos de Documento

El modelo `DriverDocumentModel` (`logistics_driver_documents`) gestiona la acreditación documental de competencias técnicas del conductor, certificaciones normativas de seguridad (Manejo Defensivo, Primeros Auxilios, Hazmat) y la constancia de Aptitud Médica Ocupacional.

---

## Tipos Documentales Soportados (`DriverDocumentType`)

- **`DEFENSIVE_DRIVING_CERTIFICATE`**: Certificado de Curso de Manejo Defensivo.
- **`HAZMAT_CERTIFICATE`**: Acreditación para Transporte de Materiales y Residuos Peligrosos (Reglamento MTC / SUCAMEC).
- **`MEDICAL_FITNESS_CERTIFICATE`**: Certificado de Aptitud Médica Ocupacional para Conducción.
- **`CRIMINAL_RECORD_CERTIFICATE`**: Certificado de Antecedentes Penales / Policiales.
- **`SCTR_INSURANCE`**: Seguro Complementario de Trabajo de Riesgo (Salud y Pensión).
- **`OTHER`**: Otros certificados o capacitaciones de seguridad de cliente/planta.

---

## Esquema SQL de `logistics_driver_documents`

```sql
CREATE TABLE logistics_driver_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    document_type VARCHAR(40) NOT NULL,
    document_number VARCHAR(100) NULL,
    issuing_entity VARCHAR(150) NOT NULL,
    
    issued_at DATE NOT NULL,
    expires_at DATE NULL,
    
    medical_fitness_status VARCHAR(30) NULL, -- FIT, FIT_WITH_RESTRICTIONS, UNFIT (Solo para MEDICAL_FITNESS_CERTIFICATE)
    file_reference_id UUID NULL,
    
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_driver_doc_type_num UNIQUE (driver_id, document_type, document_number)
);

CREATE INDEX idx_driver_docs_driver ON logistics_driver_documents(driver_id, document_type);
CREATE INDEX idx_driver_docs_expires ON logistics_driver_documents(expires_at);
```

---

## Atributos SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class DriverDocumentType(str, Enum):
    DEFENSIVE_DRIVING_CERTIFICATE = "DEFENSIVE_DRIVING_CERTIFICATE"
    HAZMAT_CERTIFICATE = "HAZMAT_CERTIFICATE"
    MEDICAL_FITNESS_CERTIFICATE = "MEDICAL_FITNESS_CERTIFICATE"
    CRIMINAL_RECORD_CERTIFICATE = "CRIMINAL_RECORD_CERTIFICATE"
    SCTR_INSURANCE = "SCTR_INSURANCE"
    OTHER = "OTHER"

class MedicalFitnessStatus(str, Enum):
    FIT = "FIT"
    FIT_WITH_RESTRICTIONS = "FIT_WITH_RESTRICTIONS"
    UNFIT = "UNFIT"

class DriverDocumentModel(Base):
    __tablename__ = "logistics_driver_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    document_type: Mapped[DriverDocumentType] = mapped_column(String(40), nullable=False)
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issuing_entity: Mapped[str] = mapped_column(String(150), nullable=False)
    
    issued_at: Mapped[date] = mapped_column(Date, nullable=False)
    expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    medical_fitness_status: Mapped[Optional[MedicalFitnessStatus]] = mapped_column(String(30), nullable=True)
    file_reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="documents")

    @property
    def is_valid(self) -> bool:
        """Determina si el documento no está vencido."""
        if not self.expires_at:
            return True
        return self.expires_at >= date.today()
```

---

## Privacidad de Datos Médicos (Protección Ley 29733)

1. **Ausencia de Diagnósticos Clínicos**: Queda prohibido registrar enfermedades, observaciones médicas privadas, resultados de laboratorio o detalles patológicos en la base de datos.
2. **Metadata Exclusiva de Aptitud**: Únicamente se registra el resultado formal emitido por el centro médico ocupacional (`FIT`, `FIT_WITH_RESTRICTIONS` o `UNFIT`) y la fecha de expiración del examen.
