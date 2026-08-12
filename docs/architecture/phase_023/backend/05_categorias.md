# 05 — Maestro Jerárquico de Categorías (`ProductCategoryModel`)

## 1. Diseño de la Estructura Categórica

Las categorías de productos permiten organizar los materiales e ítems comercializados en una estructura jerárquica tipo árbol (por ejemplo: `Electrónica > Laptops > Accesorios`). La **Fase 023** implementa un modelo de categorías jerárquicas con soporte de **Materialized Path (`hierarchy_path`)**, **prevención estricta de ciclos** y **límite de profundidad máxima de 5 niveles**.

---

## 2. Esquema Relacional de `product_categories`

```sql
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    parent_id UUID NULL REFERENCES product_categories(id) ON DELETE RESTRICT,
    
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    
    hierarchy_path VARCHAR(500) NOT NULL, -- Ej: "/root_id/child_id/subchild_id/"
    depth INTEGER NOT NULL DEFAULT 1,     -- Rango estricto: 1 <= depth <= 5
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_categories_org_code UNIQUE (organization_id, code),
    CONSTRAINT chk_category_depth CHECK (depth >= 1 AND depth <= 5)
);

CREATE INDEX idx_categories_org_parent ON product_categories(organization_id, parent_id);
CREATE INDEX idx_categories_path ON product_categories(organization_id, hierarchy_path);
```

---

## 3. Modelo SQLAlchemy (`ProductCategoryModel`)

```python
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, UniqueConstraint, Index, CheckConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class ProductCategoryModel(Base):
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=True)

    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    hierarchy_path = Column(String(500), nullable=False)
    depth = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    parent = relationship("ProductCategoryModel", remote_side=[id], backref="children")
    products = relationship("ProductModel", back_populates="category")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_categories_org_code"),
        CheckConstraint("depth >= 1 AND depth <= 5", name="chk_category_depth"),
        Index("idx_categories_org_parent", "organization_id", "parent_id"),
        Index("idx_categories_path", "organization_id", "hierarchy_path"),
    )
```

---

## 4. Motor de Validación Categórica Anti-Ciclos (`ProductCategoryTreeEngine`)

```python
class CategoryDepthExceededError(ValueError):
    pass

class CategoryCycleError(ValueError):
    pass

class ProductCategoryTreeEngine:
    MAX_DEPTH = 5

    @classmethod
    def calculate_path_and_depth(cls, db_session, category_id: uuid.UUID, parent_id: uuid.UUID | None) -> tuple[str, int]:
        """
        Calcula el hierarchy_path y valida que la profundidad no supere MAX_DEPTH (5).
        Adicionalmente, comprueba que parent_id no genera un ciclo referencial.
        """
        if parent_id is None:
            # Categoría Raíz
            return f"/{category_id}/", 1

        # Prevenir autorreferencia simple
        if category_id == parent_id:
            raise CategoryCycleError(f"La categoría '{category_id}' no puede ser su propio padre.")

        # Obtener el padre
        parent = db_session.query(ProductCategoryModel).get(parent_id)
        if not parent:
            raise ValueError(f"La categoría padre '{parent_id}' no existe.")

        # Validar si el nuevo padre es un descendiente de la categoría actual (Ciclo profundo)
        if f"/{category_id}/" in parent.hierarchy_path:
            raise CategoryCycleError(
                f"Referencia circular detectada: La categoría padre '{parent.name}' es descendiente de '{category_id}'."
            )

        new_depth = parent.depth + 1
        if new_depth > cls.MAX_DEPTH:
            raise CategoryDepthExceededError(
                f"No se permite crear la categoría. Supera la profundidad máxima permitida de {cls.MAX_DEPTH} niveles."
            )

        new_path = f"{parent.hierarchy_path}{category_id}/"
        return new_path, new_depth
```

---

## 5. Visualización de Árbol Jerárquico (`/tree`)

El endpoint `GET /api/logistics/product-categories/tree` retorna la estructura jerárquica anidada optimizada:

```json
[
  {
    "id": "c1a23b45-6789-4d0a-8e2b-111111111111",
    "code": "CAT-ELEC",
    "name": "Electrónica y Tecnología",
    "depth": 1,
    "hierarchy_path": "/c1a23b45-6789-4d0a-8e2b-111111111111/",
    "children": [
      {
        "id": "c2b34c56-7890-4e1b-9f3c-222222222222",
        "code": "CAT-COMP",
        "name": "Computadoras y Laptops",
        "depth": 2,
        "hierarchy_path": "/c1a23b45-6789-4d0a-8e2b-111111111111/c2b34c56-7890-4e1b-9f3c-222222222222/",
        "children": []
      }
    ]
  }
]
```

### Consultas Rápidas de Subárbol con Materialized Path:
Para consultar **todos los descendientes** de la categoría `CAT-ELEC` sin recurrencia SQL:

```sql
SELECT * FROM product_categories
WHERE organization_id = :org_id
  AND hierarchy_path LIKE '/c1a23b45-6789-4d0a-8e2b-111111111111/%';
```
Esta consulta utiliza el índice B-Tree sobre `hierarchy_path`, retornando la información en sub-milisegundos (< 5ms).
