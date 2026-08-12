"""Product versioning application service for Phase 023."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import ProductModel, ProductVersionModel


class ProductVersionService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def compute_content_hash(payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def create_version(
        self,
        product: ProductModel,
        version_name: str = "1.0.0",
        user_id: Optional[UUID] = None,
    ) -> ProductVersionModel:
        # Build category snapshot
        cat_snap = {
            "id": str(product.category.id),
            "code": product.category.code,
            "name": product.category.name,
            "hierarchy_path": product.category.hierarchy_path,
        }
        brand_snap = None
        if product.brand:
            brand_snap = {
                "id": str(product.brand.id),
                "code": product.brand.code,
                "name": product.brand.name,
            }

        payload = {
            "sku": product.sku,
            "name": product.name,
            "product_type": product.product_type,
            "base_unit_code": product.base_unit_code,
            "category": cat_snap,
            "brand": brand_snap,
        }

        c_hash = self.compute_content_hash(payload)

        pv = ProductVersionModel(
            product_id=product.id,
            version=version_name,
            status="DRAFT",
            sku_snapshot=product.sku,
            name=product.name,
            description=product.description,
            category_snapshot=cat_snap,
            brand_snapshot=brand_snap,
            product_type=product.product_type,
            base_unit_code=product.base_unit_code,
            content_hash=c_hash,
            effective_from=datetime.now(timezone.utc),
            created_by=user_id,
        )
        self.db.add(pv)
        self.db.commit()
        self.db.refresh(pv)
        return pv

    def activate_version(self, version_id: UUID, user_id: Optional[UUID] = None) -> ProductVersionModel:
        pv = self.db.get(ProductVersionModel, version_id)
        if not pv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")

        # Deprecate previous active versions
        self.db.execute(
            update(ProductVersionModel)
            .where(
                ProductVersionModel.product_id == pv.product_id,
                ProductVersionModel.status == "ACTIVE",
            )
            .values(status="DEPRECATED", effective_to=datetime.now(timezone.utc))
        )

        pv.status = "ACTIVE"
        pv.approved_by = user_id
        pv.approved_at = datetime.now(timezone.utc)

        # Update product reference
        product = self.db.get(ProductModel, pv.product_id)
        if product:
            product.active_version_id = pv.id

        self.db.commit()
        self.db.refresh(pv)
        return pv

    def list_versions(self, product_id: UUID) -> List[ProductVersionModel]:
        stmt = select(ProductVersionModel).where(
            ProductVersionModel.product_id == product_id
        ).order_by(ProductVersionModel.created_at.desc())
        return list(self.db.scalars(stmt).all())
