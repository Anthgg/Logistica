# 06 — Maestro de Marcas (`ProductBrandModel`)

## 1. Justificación Arquitectónica del Desacoplamiento de Marcas

En los sistemas de inventario y WMS tradicionales, el atributo "Marca" suele almacenarse como una simple cadena de texto libre (`VARCHAR`) dentro del producto o mezclado con los registros de proveedores/fabricantes (*Business Partners*). Esto genera graves problemas de consistencia:

- Inconsistencia de nombres (ej. `Sony`, `SONY INC.`, `sony`, `Sony Corp`).
- Imposibilidad de realizar analíticas de stock por marca comercial.
- Acoplamiento incorrecto entre la marca de un producto y el distribuidor/proveedor que lo suministra (Fase 025). Un producto marca "Apple" puede ser suministrado por 5 proveedores distintos.

La **Fase 023** resuelve este problema mediante una entidad independiente `ProductBrandModel` que impone un **nombre normalizado único por organización**.

---

## 2. Esquema Relacional de `product_brands`

```sql
CREATE TABLE product_brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    website_url VARCHAR(255) NULL,
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_brands_org_normalized_name UNIQUE (organization_id, normalized_name)
);

CREATE INDEX idx_brands_org_lookup ON product_brands(organization_id, normalized_name);
```

---

## 3. Modelo SQLAlchemy (`ProductBrandModel`)

```python
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, UniqueConstraint, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base
from app.core.utils import normalize_text_upper

class ProductBrandModel(Base):
    __tablename__ = "product_brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    normalized_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    products = relationship("ProductModel", back_populates="brand")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_name", name="uq_brands_org_normalized_name"),
        Index("idx_brands_org_lookup", "organization_id", "normalized_name"),
    )
```

---

## 4. Normalización y Prevención de Duplicados

Al registrar o editar una marca en el servicio `ProductBrandService`, el campo `normalized_name` procesa la cadena aplicando descarte de espacios extras, tildes y conversión a mayúsculas:

```python
def normalize_brand_name(raw_name: str) -> str:
    if not raw_name or not raw_name.strip():
        raise ValueError("El nombre de la marca no puede estar vacío.")
    
    clean = raw_name.strip()
    # Remover tildes y diacríticos
    clean = unicodedata.normalize('NFD', clean)
    clean = "".join([c for c in clean if unicodedata.category(c) != 'Mn'])
    # Convertir a mayúsculas y colapsar espacios
    normalized = re.sub(r"\s+", " ", clean.upper())
    return normalized
```

### Ejemplos de Equivalencias Normalizadas:

| Nombre Ingresado (`name`) | Nombre Normalizado (`normalized_name`) | Resultado |
| :--- | :--- | :--- |
| `Samsung` | `SAMSUNG` | Insertado correctamente |
| `SAMSUNG ELECTRONICS` | `SAMSUNG ELECTRONICS` | Insertado correctamente |
| `samsung` | `SAMSUNG` | **Rechazado** (`409 Conflict: La marca ya existe`) |
| `Sámsung ` | `SAMSUNG` | **Rechazado** (`409 Conflict: La marca ya existe`) |

---

## 5. Desacoplamiento de Socios Comerciales (Fase 025)

El modelo de marcas en la Fase 023 está estrictamente desacoplado del maestro de proveedores/socios comerciales (Fase 025). La relación entre un `ProductModel`, su `ProductBrandModel` y los proveedores que lo despachan se modelará en la Fase 025 a través de una entidad intermedia `SupplierProductCatalogModel`.

```mermaid
graph LR
    P[ProductModel] -->|Tiene Marca| B[ProductBrandModel]
    S[SupplierModel (Fase 025)] -->|Suministra| SPC[SupplierProductCatalogModel (Fase 025)]
    P -->|Se Cotiza en| SPC
```
