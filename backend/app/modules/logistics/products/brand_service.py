"""Brand management application service for Phase 023."""

import re
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import ProductBrandModel


class ProductBrandService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def normalize_name(name: str) -> str:
        s = name.strip().upper()
        return re.sub(r"\s+", " ", s)

    def create_brand(
        self,
        organization_id: UUID,
        code: str,
        name: str,
        description: Optional[str] = None,
        manufacturer_name: Optional[str] = None,
        country_code: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductBrandModel:
        clean_code = code.strip().upper()
        norm_name = self.normalize_name(name)

        # Check code uniqueness
        stmt_code = select(ProductBrandModel).where(
            ProductBrandModel.organization_id == organization_id,
            ProductBrandModel.code == clean_code,
        )
        if self.db.scalar(stmt_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand code '{clean_code}' already exists in this organization.",
            )

        # Check name uniqueness
        stmt_name = select(ProductBrandModel).where(
            ProductBrandModel.organization_id == organization_id,
            ProductBrandModel.normalized_name == norm_name,
        )
        if self.db.scalar(stmt_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand name '{name}' already exists in this organization.",
            )

        brand = ProductBrandModel(
            organization_id=organization_id,
            code=clean_code,
            name=name.strip(),
            normalized_name=norm_name,
            description=description,
            manufacturer_name=manufacturer_name,
            country_code=country_code.upper() if country_code else None,
            status="ACTIVE",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def list_brands(self, organization_id: UUID) -> List[ProductBrandModel]:
        stmt = select(ProductBrandModel).where(
            ProductBrandModel.organization_id == organization_id
        ).order_by(ProductBrandModel.name)
        return list(self.db.scalars(stmt).all())
