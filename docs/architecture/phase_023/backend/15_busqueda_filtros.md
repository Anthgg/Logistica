# 15 — Motor de Búsqueda, Filtrado y Paginación Optimizada

## 1. Diseño del Motor de Búsqueda de Productos

El Catálogo de Productos en un WMS de escala empresarial requiere capacidades de búsqueda de alta velocidad sobre millones de registros, soportando filtros combinados por parámetros estructurados (categoría, marca, estado, tipo de producto) y búsquedas difusas/exactas por términos libres (SKU, SKU alias, nombre, código de barras GTIN/EAN).

La **Fase 023** implementa una capa de consulta optimizada basada en SQLAlchemy `Select` dinámico indexado.

---

## 2. Parámetros de Filtrado y Búsqueda

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ProductSortField(str, Enum):
    CREATED_AT = "created_at"
    SKU = "sku"
    NAME = "name"
    STATUS = "status"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class ProductFilterParams(BaseModel):
    query: Optional[str] = Field(None, description="Término libre: SKU, Alias, Nombre o Código de Barras")
    category_id: Optional[str] = Field(None, description="UUID de categoría (incluye descendientes si include_subcategories=True)")
    include_subcategories: bool = Field(True, description="Si es True, incluye categorías hijas usando hierarchy_path")
    brand_id: Optional[str] = Field(None, description="UUID de marca")
    product_type: Optional[str] = Field(None, description="Filtro por tipo de producto (ej. FINISHED_GOOD)")
    status: Optional[str] = Field(None, description="Filtro por estado (ej. ACTIVE)")
    is_hazmat: Optional[bool] = Field(None, description="Filtro por marca Hazmat")
    requires_cold_chain: Optional[bool] = Field(None, description="Filtro por requerimiento de cadena de frío")
    
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(20, ge=1, le=100, description="Tamaño de página (máx 100)")
    sort_by: ProductSortField = Field(ProductSortField.CREATED_AT)
    sort_order: SortOrder = Field(SortOrder.DESC)
```

---

## 3. Construcción Dinámica de la Consulta SQL (`ProductSearchEngine`)

```python
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

class ProductSearchEngine:

    @classmethod
    def build_query(cls, db_session, org_id: uuid.UUID, params: ProductFilterParams):
        # Base query con Aislamiento Multi-Tenant por Organización
        stmt = select(ProductModel).where(ProductModel.organization_id == org_id)

        # 1. Búsqueda Libre por Término (Query Text)
        if params.query and params.query.strip():
            raw_q = params.query.strip()
            norm_q = ProductSKUValidator.normalize_sku(raw_q) if len(raw_q) >= 2 else raw_q.upper()
            search_pattern = f"%{raw_q}%"

            # Subconsulta de IDs por alias o identificador de barras
            alias_subq = (
                select(ProductSKUAliasModel.product_id)
                .where(ProductSKUAliasModel.organization_id == org_id)
                .where(ProductSKUAliasModel.normalized_alias_sku.like(f"%{norm_q}%"))
            )

            id_subq = (
                select(ProductIdentifierModel.product_id)
                .where(ProductIdentifierModel.organization_id == org_id)
                .where(ProductIdentifierModel.normalized_value.like(f"%{norm_q}%"))
            )

            stmt = stmt.where(
                or_(
                    ProductModel.normalized_sku.like(f"%{norm_q}%"),
                    ProductModel.name.ilike(search_pattern),
                    ProductModel.id.in_(alias_subq),
                    ProductModel.id.in_(id_subq)
                )
            )

        # 2. Filtro por Categoría y Sub-árbol Categórico
        if params.category_id:
            if params.include_subcategories:
                cat = db_session.query(ProductCategoryModel).get(params.category_id)
                if cat:
                    # Usar el materialized path para incluir subcategorías de forma ultra-rápida
                    path_pattern = f"{cat.hierarchy_path}%"
                    cat_ids_subq = (
                        select(ProductCategoryModel.id)
                        .where(ProductCategoryModel.organization_id == org_id)
                        .where(ProductCategoryModel.hierarchy_path.like(path_pattern))
                    )
                    stmt = stmt.where(ProductModel.category_id.in_(cat_ids_subq))
            else:
                stmt = stmt.where(ProductModel.category_id == params.category_id)

        # 3. Filtros Estructurados Directos
        if params.brand_id:
            stmt = stmt.where(ProductModel.brand_id == params.brand_id)
        if params.product_type:
            stmt = stmt.where(ProductModel.product_type == params.product_type)
        if params.status:
            stmt = stmt.where(ProductModel.status == params.status)
        if params.is_hazmat is not None:
            stmt = stmt.where(ProductModel.is_hazmat == params.is_hazmat)
        if params.requires_cold_chain is not None:
            stmt = stmt.where(ProductModel.requires_cold_chain == params.requires_cold_chain)

        # 4. Carga Eficiente de Relaciones (Eager Loading N+1 Avoidance)
        stmt = stmt.options(
            selectinload(ProductModel.category),
            selectinload(ProductModel.brand),
            selectinload(ProductModel.identifiers),
            selectinload(ProductModel.physical_profile)
        )

        return stmt
```

---

## 4. Paginación Eficiente de Resultados

Para garantizar tiempos de respuesta inferiores a 20ms en tablas con > 500,000 productos:

```python
def paginate_search(db_session, org_id: uuid.UUID, params: ProductFilterParams):
    base_stmt = ProductSearchEngine.build_query(db_session, org_id, params)

    # 1. Total de registros para metadatos de paginación
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_records = db_session.execute(count_stmt).scalar() or 0

    # 2. Aplicar Ordenamiento y Paginación OFFSET/LIMIT
    sort_column = getattr(ProductModel, params.sort_by.value)
    if params.sort_order == SortOrder.DESC:
        sort_column = sort_column.desc()

    paginated_stmt = (
        base_stmt
        .order_by(sort_column)
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )

    items = db_session.execute(paginated_stmt).scalars().all()
    total_pages = (total_records + params.page_size - 1) // params.page_size

    return {
        "items": items,
        "total": total_records,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages
    }
```

---

## 5. Formato de Respuesta REST (`PaginatedProductResponse`)

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "sku": "PROD-LAPTOP-001",
      "normalized_sku": "PROD-LAPTOP-001",
      "name": "Laptop Corporativa i7 16GB",
      "product_type": "FINISHED_GOOD",
      "status": "ACTIVE",
      "base_unit_code": "UND",
      "category": {
        "id": "c2b34c56-7890-4e1b-9f3c-222222222222",
        "code": "CAT-COMP",
        "name": "Computadoras y Laptops"
      },
      "brand": {
        "id": "b1a23b45-6789-4d0a-8e2b-999999999999",
        "name": "Dell"
      },
      "row_version": 3,
      "created_at": "2026-07-28T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```
