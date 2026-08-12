# 11 — Fotografías del Conductor y Políticas de Privacidad (`DriverPhotoModel`)

## Privacidad de Datos e Imágenes de Identificación

El almacenamiento de fotografías de perfil y de licencias físicas involucra datos sensibles de privacidad (Ley 29733 / GDPR). La plataforma prohíbe terminantemente el almacenamiento de cadenas en Base64 en tablas relacionales SQL, así como la derivación o guardado de plantillas/embeddings biométricos en la base de datos de maestros.

---

## Modelo `DriverPhotoModel` (`logistics_driver_photos`)

```sql
CREATE TABLE logistics_driver_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    photo_type VARCHAR(30) NOT NULL DEFAULT 'PROFILE', -- PROFILE, LICENSE_FRONT, LICENSE_BACK, BADGE
    file_reference_id UUID NOT NULL, -- ID de referencia al servicio de archivos (Object Storage / MinIO)
    
    mime_type VARCHAR(50) NOT NULL DEFAULT 'image/jpeg',
    file_size_bytes INT NOT NULL,
    sha256_checksum VARCHAR(64) NOT NULL,
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploaded_by UUID NULL REFERENCES sys_users(id)
);

CREATE INDEX idx_driver_photos_driver ON logistics_driver_photos(driver_id, photo_type);
```

---

## Atributos SQLAlchemy

```python
from enum import Enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class PhotoType(str, Enum):
    PROFILE = "PROFILE"
    LICENSE_FRONT = "LICENSE_FRONT"
    LICENSE_BACK = "LICENSE_BACK"
    BADGE = "BADGE"

class DriverPhotoModel(Base):
    __tablename__ = "logistics_driver_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    photo_type: Mapped[PhotoType] = mapped_column(String(30), default=PhotoType.PROFILE, nullable=False)
    file_reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    mime_type: Mapped[str] = mapped_column(String(50), default="image/jpeg", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True)

    driver = relationship("DriverModel", back_populates="photos")
```

---

## Políticas Estrictas de Almacenamiento y Privacidad

1. **Referencia Opaca (`file_reference_id`)**: La tabla sólo almacena un UUID opaco que apunta al objeto cifrado en Object Storage. La URL firmada (Presigned URL) de lectura se genera dinámicamente con tiempo de expiración corto (máximo 15 minutos).
2. **Prohibición de Base64**: No se admiten datos BLOB ni Base64 dentro del motor SQL para prevenir fragmentación de tablas e hinchamiento de respaldos (backup bloat).
3. **Ausencia de Biometría Facial**: Queda expresamente prohibido derivar o guardar descriptores vectoriales o plantillas de reconocimiento facial dentro de `DriverPhotoModel`.
4. **Política de Retención y Depuración**: Cuando un conductor es marcado como `ARCHIVED`, las imágenes asociadas entran en período de retención legal (5 años) tras el cual son eliminadas físicamente del Object Storage mediante job de purga asíncrono.
