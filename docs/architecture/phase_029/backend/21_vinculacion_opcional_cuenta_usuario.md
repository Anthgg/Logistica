# 21 — Vinculación Opcional con Cuenta de Usuario (`DriverUserAccountLinkModel`)

## Propósito del Enlace Conductor-Usuario

Cuando un conductor necesita utilizar la **Aplicación Móvil del Conductor** (App de Despacho, firma digital de guías de remisión, reporte de checklist pre-operacional y telemetría), requiere contar con una cuenta de usuario (`User`).

El modelo **`DriverUserAccountLinkModel`** (`logistics_driver_user_account_links`) gestiona este enlace opcional, seguro y 1:1.

---

## Esquema SQL de `logistics_driver_user_account_links`

```sql
CREATE TABLE logistics_driver_user_account_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL UNIQUE REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL UNIQUE REFERENCES sys_users(id) ON DELETE CASCADE,
    
    linked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    linked_by UUID NOT NULL REFERENCES sys_users(id),
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    unlinked_at TIMESTAMPTZ NULL,
    unlinked_by UUID NULL REFERENCES sys_users(id),
    unlink_reason TEXT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_driver_user_link_driver ON logistics_driver_user_account_links(driver_id);
CREATE UNIQUE INDEX idx_driver_user_link_user ON logistics_driver_user_account_links(user_id);
```

---

## Atributos SQLAlchemy

```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class DriverUserAccountLinkModel(Base):
    __tablename__ = "logistics_driver_user_account_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    linked_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unlinked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unlinked_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True)
    unlink_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="user_link")
```

---

## Reglas de Vinculación y Desvinculación

1. **Relación Unívoca Strictly 1:1**: Un `Driver` solo puede enlazarse a una cuenta de `User` activa, y una cuenta de `User` solo puede pertenecer a un `Driver`.
2. **Validación de Organización**: El servicio valida que la cuenta `User` pertenezca a la misma `organization_id` que el `Driver`.
3. **Auditoría de Desvinculación**: Al revocar el enlace, el registro no se borra física ni lógicamente; se desactiva `is_active = FALSE`, se graba `unlinked_at` y el motivo, permitiendo vincular una nueva cuenta de usuario en el futuro sin romper el historial de acciones pasadas.
