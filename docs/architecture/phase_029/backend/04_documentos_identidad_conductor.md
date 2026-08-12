# 04 — Documentos de Identidad del Conductor (`DriverIdentityDocumentModel`)

## Definición y Tipos Admitidos

El modelo `DriverIdentityDocumentModel` (`logistics_driver_identity_documents`) almacena los documentos oficiales de identidad del conductor.

### Tipos de Documentos Soportados (`IdentityDocumentType`):
- **`DNI`**: Documento Nacional de Identidad (Perú, 8 dígitos numéricos).
- **`CE`**: Carnet de Extranjería (9 a 12 caracteres alfanuméricos).
- **`PASSPORT`**: Pasaporte Internacional.
- **`PTP`**: Permiso Temporal de Permanencia.
- **`OTHER`**: Otro documento oficial de identidad de país extranjero.

---

## Esquema SQL de `logistics_driver_identity_documents`

```sql
CREATE TABLE logistics_driver_identity_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    document_type VARCHAR(20) NOT NULL, -- DNI, CE, PASSPORT, etc.
    document_number VARCHAR(50) NOT NULL,
    normalized_document_number VARCHAR(50) NOT NULL,
    masked_document_number VARCHAR(50) NOT NULL,
    
    issuing_country VARCHAR(3) NOT NULL DEFAULT 'PER',
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'UNVERIFIED', -- UNVERIFIED, VERIFIED, REJECTED
    
    issued_at DATE NULL,
    expires_at DATE NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_driver_doc_type UNIQUE (driver_id, document_type),
    CONSTRAINT uq_doc_type_number UNIQUE (document_type, normalized_document_number)
);

CREATE INDEX idx_identity_doc_normalized ON logistics_driver_identity_documents(normalized_document_number);
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

class IdentityDocumentType(str, Enum):
    DNI = "DNI"
    CE = "CE"
    PASSPORT = "PASSPORT"
    PTP = "PTP"
    OTHER = "OTHER"

class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class DriverIdentityDocumentModel(Base):
    __tablename__ = "logistics_driver_identity_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    document_type: Mapped[IdentityDocumentType] = mapped_column(String(20), nullable=False)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    masked_document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    issuing_country: Mapped[str] = mapped_column(String(3), default="PER", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(String(30), default=VerificationStatus.UNVERIFIED, nullable=False)
    
    issued_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="identity_documents")

    __table_args__ = (
        UniqueConstraint("driver_id", "document_type", name="uq_driver_doc_type"),
        UniqueConstraint("document_type", "normalized_document_number", name="uq_doc_type_number"),
    )
```

---

## Normalización y Enmascaramiento de Privacidad

En cumplimiento de las normativas de protección de datos personales (LPDP Ley 29733 / GDPR), el número de documento de identidad **nunca se retorna sin enmascarar en respuestas generales de la API**.

### Algoritmo de Enmascaramiento:

```python
class IdentityDocumentMasker:

    @classmethod
    def normalize(cls, raw_number: str) -> str:
        """Elimina espacios, guiones y convierte a mayúsculas."""
        if not raw_number:
            return ""
        return re.sub(r"[^A-Z0-9]", "", raw_number.strip().upper())

    @classmethod
    def mask(cls, normalized_number: str) -> str:
        """
        Enmascara el documento mostrando únicamente los últimos 3 dígitos.
        Ejemplo DNI '72849153' -> '*****153'
        Ejemplo CE '001234567' -> '******567'
        """
        if not normalized_number:
            return ""
        length = len(normalized_number)
        if length <= 3:
            return "*" * length
        visible_digits = 3
        masked_part = "*" * (length - visible_digits)
        unmasked_part = normalized_number[-visible_digits:]
        return f"{masked_part}{unmasked_part}"
```

### Reglas de Revelación de Documento (Step-Up Security):
1. Por defecto, todas las respuestas JSON de endpoints ordinarios (`GET /drivers`, `GET /drivers/{id}`) retornan el campo `document_number` con el valor de `masked_document_number` (ej. `*****153`).
2. Para obtener el número completo sin enmascarar, el usuario solicitante debe poseer el permiso explícito **`logistics.drivers.sensitive.read`** Y realizar una solicitud Step-Up con token firmado de verificación o re-autenticación.
3. Toda revelación de documento sin enmascarar registra inmediatamente un evento de auditoría crítico de lectura sensible en `logistics_audit_events`.
