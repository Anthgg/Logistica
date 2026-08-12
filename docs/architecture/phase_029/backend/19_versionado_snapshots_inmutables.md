# 19 — Versionado e Historización mediante Snapshots Inmutables (`DriverVersionModel`)

## Propósito del Versionado Histórico Inmutable

Para cumplir con auditorías forenses, requerimientos legales en accidentes de tránsito e inspecciones del MTC / SUTRAN, es imprescindible conocer el **estado exacto e inalterable que tenía el expediente de un conductor en cualquier instante del tiempo**.

El modelo `DriverVersionModel` (`logistics_driver_versions`) almacena un **snapshot completo en JSONB** de la entidad `Driver` y sus tablas secundarias cada vez que ocurre una mutación significativa, sellado con un hash criptográfico **SHA-256 (`content_hash`)**.

---

## Esquema SQL de `logistics_driver_versions`

```sql
CREATE TABLE logistics_driver_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES logistics_drivers(id) ON DELETE CASCADE,
    
    version_number INT NOT NULL,
    snapshot_data JSONB NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 del contenido JSONB ordenado
    
    change_reason VARCHAR(255) NOT NULL,
    changed_by UUID NOT NULL REFERENCES sys_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_driver_version UNIQUE (driver_id, version_number)
);

CREATE INDEX idx_driver_versions_driver ON logistics_driver_versions(driver_id, version_number DESC);
```

---

## Atributos SQLAlchemy

```python
import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base_class import Base

class DriverVersionModel(Base):
    __tablename__ = "logistics_driver_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_drivers.id", ondelete="CASCADE"), nullable=False)
    
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    driver = relationship("DriverModel", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("driver_id", "version_number", name="uq_driver_version"),
    )

    @classmethod
    def compute_sha256(cls, data: Dict[str, Any]) -> str:
        """Calcula el hash SHA-256 determinista serializando la estructura JSON con llaves ordenadas."""
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
```

---

## Estructura del Snapshot JSONB

```json
{
  "driver_id": "8f8b89e3-4f3b-48c9-94b2-03f90b17849e",
  "driver_code": "DRV-000042",
  "first_name": "Juan Carlos",
  "last_name": "Pérez Gomez",
  "display_name": "Juan Carlos Pérez Gomez",
  "lifecycle_status": "ACTIVE",
  "compliance_status": "COMPLIANT",
  "eligibility_status": "ELIGIBLE",
  "row_version": 4,
  "identity_documents": [
    {
      "document_type": "DNI",
      "masked_document_number": "*****153",
      "verification_status": "VERIFIED"
    }
  ],
  "licenses": [
    {
      "masked_license_number": "****9153",
      "status": "VALID",
      "categories": ["A-IIIb", "A-IIIc"],
      "restrictions": ["REST_CORRECTIVE_LENSES"]
    }
  ],
  "documents": [
    {
      "document_type": "HAZMAT_CERTIFICATE",
      "expires_at": "2027-12-31"
    }
  ]
}
```

---

## Verificación Criptográfica de Integridad

Durante una auditoría, el sistema puede verificar la no manipulación del histórico recalculando `compute_sha256(snapshot_data)` y comparándolo con el valor almacenado en `content_hash`. Cualquier discrepancia señala alteración no autorizada de la base de datos.
