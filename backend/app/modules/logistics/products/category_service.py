"""Category management application service for Phase 023."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import ProductCategoryModel


class ProductCategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(
        self,
        organization_id: UUID,
        code: str,
        name: str,
        description: Optional[str] = None,
        parent_category_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductCategoryModel:
        clean_code = code.strip().upper()
        # Uniqueness check
        stmt = select(ProductCategoryModel).where(
            ProductCategoryModel.organization_id == organization_id,
            ProductCategoryModel.code == clean_code,
        )
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category code '{clean_code}' already exists in this organization.",
            )

        hierarchy_path = clean_code
        depth = 1

        if parent_category_id:
            parent = self.db.get(ProductCategoryModel, parent_category_id)
            if not parent or parent.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found in organization.",
                )
            if parent.depth >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum category hierarchy depth (5) exceeded.",
                )
            hierarchy_path = f"{parent.hierarchy_path}/{clean_code}"
            depth = parent.depth + 1

        cat = ProductCategoryModel(
            organization_id=organization_id,
            parent_category_id=parent_category_id,
            code=clean_code,
            name=name.strip(),
            description=description,
            hierarchy_path=hierarchy_path,
            depth=depth,
            status="ACTIVE",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def get_category_tree(self, organization_id: UUID) -> List[Dict[str, Any]]:
        stmt = select(ProductCategoryModel).where(
            ProductCategoryModel.organization_id == organization_id
        ).order_by(ProductCategoryModel.hierarchy_path)
        categories = list(self.db.scalars(stmt).all())

        cat_map: Dict[UUID, Dict[str, Any]] = {}
        tree: List[Dict[str, Any]] = []

        for c in categories:
            node = {
                "id": str(c.id),
                "code": c.code,
                "name": c.name,
                "description": c.description,
                "hierarchy_path": c.hierarchy_path,
                "depth": c.depth,
                "status": c.status,
                "children": [],
            }
            cat_map[c.id] = node
            if c.parent_category_id and c.parent_category_id in cat_map:
                cat_map[c.parent_category_id]["children"].append(node)
            else:
                tree.append(node)

        return tree

    def list_categories(self, organization_id: UUID) -> List[ProductCategoryModel]:
        stmt = select(ProductCategoryModel).where(
            ProductCategoryModel.organization_id == organization_id
        ).order_by(ProductCategoryModel.code)
        return list(self.db.scalars(stmt).all())
