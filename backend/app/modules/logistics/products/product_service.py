"""Product master data CRUD and lifecycle application service for Phase 023."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import (
    ProductBrandModel,
    ProductCategoryModel,
    ProductIdentifierModel,
    ProductModel,
    ProductSKUAliasModel,
)
from app.modules.logistics.products.sku_validator import ProductSKUValidator
from app.modules.logistics.products.version_service import ProductVersionService


PROVISIONAL_UNITS = {"UND", "KG", "G", "L", "ML", "M", "CM", "M2", "M3", "CAJA", "PAQUETE"}
PRODUCT_TYPES = {"PHYSICAL_GOOD", "CONSUMABLE", "RAW_MATERIAL", "FINISHED_GOOD", "COMPONENT", "PACKAGING_MATERIAL", "SPARE_PART", "SERVICE", "ASSET", "OTHER"}
PRODUCT_STATUSES = {"DRAFT", "ACTIVE", "INACTIVE", "SUSPENDED", "DISCONTINUED", "BLOCKED", "ARCHIVED"}


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.version_service = ProductVersionService(db)

    def create_product(
        self,
        organization_id: UUID,
        sku: str,
        name: str,
        category_id: UUID,
        brand_id: Optional[UUID] = None,
        product_type: str = "PHYSICAL_GOOD",
        base_unit_code: str = "UND",
        short_name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductModel:
        # Validate SKU
        is_valid, norm_sku, err = ProductSKUValidator.validate(sku)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

        if product_type not in PRODUCT_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product_type '{product_type}'.")

        unit = base_unit_code.upper()
        if unit not in PROVISIONAL_UNITS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base_unit_code '{unit}'.")

        # Uniqueness check
        stmt_sku = select(ProductModel).where(
            ProductModel.organization_id == organization_id,
            ProductModel.normalized_sku == norm_sku,
        )
        if self.db.scalar(stmt_sku):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product with SKU '{norm_sku}' already exists.")

        # Category check
        category = self.db.get(ProductCategoryModel, category_id)
        if not category or category.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found in organization.")

        # Brand check
        if brand_id:
            brand = self.db.get(ProductBrandModel, brand_id)
            if not brand or brand.organization_id != organization_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found in organization.")

        product = ProductModel(
            organization_id=organization_id,
            sku=sku.strip(),
            normalized_sku=norm_sku,
            name=name.strip(),
            short_name=short_name,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            product_type=product_type,
            base_unit_code=unit,
            status="DRAFT",
            lifecycle_status="ACTIVE",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        # Create initial draft version
        self.version_service.create_version(product, version_name="1.0.0", user_id=user_id)

        return product

    def change_sku(
        self,
        product_id: UUID,
        new_sku: str,
        reason: str,
        user_id: Optional[UUID] = None,
    ) -> ProductModel:
        product = self.db.get(ProductModel, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        is_valid, norm_sku, err = ProductSKUValidator.validate(new_sku)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

        if norm_sku == product.normalized_sku:
            return product

        # Check uniqueness
        stmt_sku = select(ProductModel).where(
            ProductModel.organization_id == product.organization_id,
            ProductModel.normalized_sku == norm_sku,
        )
        if self.db.scalar(stmt_sku):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"SKU '{norm_sku}' already exists.")

        old_sku = product.sku

        # Register alias if product is ACTIVE
        if product.status == "ACTIVE":
            alias = ProductSKUAliasModel(
                product_id=product.id,
                organization_id=product.organization_id,
                previous_sku=old_sku,
                current_sku=new_sku.strip(),
                reason=reason,
                created_by=user_id,
            )
            self.db.add(alias)

        product.sku = new_sku.strip()
        product.normalized_sku = norm_sku
        product.updated_by = user_id
        product.row_version += 1

        self.db.commit()
        self.db.refresh(product)
        return product

    def change_status(
        self,
        product_id: UUID,
        target_status: str,
        reason: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductModel:
        if target_status not in PRODUCT_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid target status '{target_status}'.")

        product = self.db.get(ProductModel, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        if target_status == "ACTIVE" and product.status == "DRAFT":
            # Activate current draft version
            stmt = select(ProductModel).where(ProductModel.id == product_id)
            if product.versions:
                self.version_service.activate_version(product.versions[0].id, user_id=user_id)

        if target_status == "ARCHIVED":
            product.archived_at = datetime.now(timezone.utc)
            product.archived_by = user_id
            product.archive_reason = reason

        product.status = target_status
        product.updated_by = user_id
        product.row_version += 1

        self.db.commit()
        self.db.refresh(product)
        return product

    def search_products(
        self,
        organization_id: UUID,
        search: Optional[str] = None,
        category_id: Optional[UUID] = None,
        brand_id: Optional[UUID] = None,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ProductModel], int]:
        query = select(ProductModel).where(ProductModel.organization_id == organization_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            # Join identifiers for barcode lookup
            query = query.outerjoin(ProductIdentifierModel).where(
                or_(
                    ProductModel.sku.ilike(term),
                    ProductModel.name.ilike(term),
                    ProductIdentifierModel.normalized_value.ilike(term),
                )
            ).distinct()

        if category_id:
            query = query.where(ProductModel.category_id == category_id)

        if brand_id:
            query = query.where(ProductModel.brand_id == brand_id)

        if product_type:
            query = query.where(ProductModel.product_type == product_type)

        if status:
            query = query.where(ProductModel.status == status)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(total_stmt) or 0

        query = query.order_by(ProductModel.sku).offset((page - 1) * page_size).limit(page_size)
        products = list(self.db.scalars(query).all())

        return products, total
