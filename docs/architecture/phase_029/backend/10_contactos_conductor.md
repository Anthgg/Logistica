# 10 — Contactos Directos y de Emergencia del Conductor (`DriverContactModel` & `DriverEmergencyContactModel`)

## Estructura de Contactos

La comunicación fluida y la gestión de contingencias en ruta requieren diferenciar claramente entre los **contactos directos operacionales** del conductor (móvil personal, correo electrónico, teléfono corporativo) y los **contactos de emergencia** (familiares, apoderados).

---

## 1. Contactos Directos (`DriverContactModel` - `logistics_driver_contacts`)

```sql
CREATE TABLE logistics_driver_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    contact_type VARCHAR(20) NOT NULL, -- MOBILE_PHONE, WORK_PHONE, PERSONAL_EMAIL, WORK_EMAIL
    contact_value VARCHAR(150) NOT NULL,
    normalized_value VARCHAR(150) NOT NULL,
    
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_driver_contact_normalized ON logistics_driver_contacts(normalized_value);
```

---

## 2. Contactos de Emergencia (`DriverEmergencyContactModel` - `logistics_driver_emergency_contacts`)

```sql
CREATE TABLE logistics_driver_emergency_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    full_name VARCHAR(150) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- SPOUSE, PARENT, CHILD, SIBLING, OTHER
    phone_number VARCHAR(30) NOT NULL,
    alternative_phone VARCHAR(30) NULL,
    address TEXT NULL,
    
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_driver_emergency_contact_driver ON logistics_driver_emergency_contacts(driver_id);
```

---

## Atributos del Modelo SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class ContactType(str, Enum):
    MOBILE_PHONE = "MOBILE_PHONE"
    WORK_PHONE = "WORK_PHONE"
    PERSONAL_EMAIL = "PERSONAL_EMAIL"
    WORK_EMAIL = "WORK_EMAIL"

class DriverContactModel(Base):
    __tablename__ = "logistics_driver_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    contact_type: Mapped[ContactType] = mapped_column(String(20), nullable=False)
    contact_value: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(150), nullable=False)
    
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="contacts")

class DriverEmergencyContactModel(Base):
    __tablename__ = "logistics_driver_emergency_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    alternative_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="emergency_contacts")
```

---

## Normalización de Teléfonos E.164 y Correos

1. **Teléfonos**: Se normalizan al estándar **E.164** (ej. `+51987654321`).
2. **Correos Electrónicos**: Se convierten a minúsculas y se remueven espacios externos (`driver@empresa.com`).
3. **Primary Unique Logic**: Sólo un contacto por tipo y un contacto de emergencia pueden tener `is_primary = TRUE`.
