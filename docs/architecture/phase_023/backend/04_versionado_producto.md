# 04 — Motor de Versionado e Inmutabilidad de Productos (`ProductVersionModel`)

## 1. Justificación del Versionado de Productos

En la logística industrial y comercial, las especificaciones de un producto (pesos, dimensiones, empaque, temperatura de almacenamiento, política de lote o código de barras) pueden variar con el tiempo. Si una orden de compra o recepción ocurrió en enero con un peso de 1.5kg, y en junio el fabricante reduce el peso a 1.2kg, la auditoría del inventario antiguo no puede verse distorsionada por las ediciones del presente.

Para garantizar la **trazabilidad histórica inmutable**, la **Fase 023** implementa el patrón de **Snapshot Versioning** alimentado por la tabla `product_versions`.

---

## 2. Esquema Relacional de `product_versions`

```sql
CREATE TABLE product_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    version_number INTEGER NOT NULL,
    content_hash CHAR(64) NOT NULL, -- Hash SHA-256 en formato Hexadecimal
    
    payload_snapshot JSONB NOT NULL,
    change_reason VARCHAR(255) NULL,
    
    effective_start TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_end TIMESTAMP WITH TIME ZONE NULL, -- NULL indica versión activa vigente
    
    created_by UUID NULL,

    CONSTRAINT uq_product_version_num UNIQUE (product_id, version_number)
);

CREATE INDEX idx_product_versions_lookup ON product_versions(product_id, version_number);
CREATE INDEX idx_product_versions_hash ON product_versions(content_hash);
CREATE INDEX idx_product_versions_validity ON product_versions(product_id, effective_start, effective_end);
```

---

## 3. Algoritmo de Hashing SHA-256 (`content_hash`)

Cada vez que se guarda una versión, el servicio serializa la totalidad de la entidad del producto y sus sub-objetos asociados (perfil físico, almacenamiento, identificadores, jerarquía) en un JSON ordenado sintácticamente por claves (*canonical JSON*), y calcula su digest SHA-256.

```python
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

class ProductVersioningService:

    @staticmethod
    def calculate_canonical_hash(payload: Dict[str, Any]) -> str:
        """
        Genera un digest SHA-256 determinístico a partir de un diccionario de atributos.
        Ordena las claves recursivamente para garantizar la idempotencia de cadenas JSON.
        """
        canonical_json = json.dumps(payload, sort_keys=True, default=str, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    @classmethod
    def create_version_snapshot(
        cls,
        db_session,
        product,
        change_reason: str,
        user_id: str
    ) -> "ProductVersionModel":
        # 1. Construir payload completo de snapshot
        snapshot_data = {
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "product_type": product.product_type,
            "status": product.status,
            "base_unit_code": product.base_unit_code,
            "category_id": str(product.category_id),
            "brand_id": str(product.brand_id) if product.brand_id else None,
            "is_hazmat": product.is_hazmat,
            "requires_cold_chain": product.requires_cold_chain,
            "is_fragile": product.is_fragile,
            "physical_profile": product.physical_profile.to_dict() if product.physical_profile else None,
            "tracking_policy": product.tracking_policy.to_dict() if product.tracking_policy else None,
            "storage_condition": product.storage_condition.to_dict() if product.storage_condition else None,
        }

        # 2. Calcular SHA-256 Digest
        content_hash = cls.calculate_canonical_hash(snapshot_data)

        # 3. Obtener el número de versión consecutivo
        last_version_num = (
            db_session.query(func.max(ProductVersionModel.version_number))
            .filter(ProductVersionModel.product_id == product.id)
            .scalar() or 0
        )
        new_version_num = last_version_num + 1

        now = datetime.utcnow()

        # 4. Cerrar la vigencia de la versión previa si existe
        if last_version_num > 0:
            db_session.query(ProductVersionModel).filter(
                ProductVersionModel.product_id == product.id,
                ProductVersionModel.effective_end.is_(None)
            ).update({"effective_end": now})

        # 5. Crear la nueva versión inmutable
        new_version = ProductVersionModel(
            organization_id=product.organization_id,
            product_id=product.id,
            version_number=new_version_num,
            content_hash=content_hash,
            payload_snapshot=snapshot_data,
            change_reason=change_reason,
            effective_start=now,
            effective_end=None,
            created_by=user_id
        )

        db_session.add(new_version)
        return new_version
```

---

## 4. Modelo SQLAlchemy (`ProductVersionModel`)

```python
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class ProductVersionModel(Base):
    __tablename__ = "product_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    version_number = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False) # SHA-256 Hex Digest

    payload_snapshot = Column(JSONB, nullable=False)
    change_reason = Column(String(255), nullable=True)

    effective_start = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_end = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)

    product = relationship("ProductModel", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("product_id", "version_number", name="uq_product_version_num"),
        Index("idx_product_versions_lookup", "product_id", "version_number"),
        Index("idx_product_versions_hash", "content_hash"),
        Index("idx_product_versions_validity", "product_id", "effective_start", "effective_end"),
    )
```

---

## 5. Ventajas Operativas del Versionado

1. **Evidencia Forense:** Firma criptográfica hash SHA-256 para demostrar ante auditorías que el registro no ha sido alterado manualmente en la base de datos.
2. **Consultas As-Of:** Capacidad de consultar cómo lucía el producto en una fecha histórica específica ejecutando:
   ```sql
   SELECT payload_snapshot FROM product_versions
   WHERE product_id = :p_id 
     AND effective_start <= :target_timestamp 
     AND (effective_end IS NULL OR effective_end > :target_timestamp);
   ```
3. **Impedimento de Modificación Directa:** La tabla `product_versions` no posee endpoints REST con verbos `PUT` o `DELETE`. Es de **solo lectura e inserción**.
