"""Quantity decomposition service for Phase 024."""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import ProductModel
from app.modules.logistics.units.models import ProductPackagingDefinitionModel, ProductUnitConfigurationModel, UnitOfMeasureModel
from app.modules.logistics.units.path_resolver import ConversionPathResolver


class QuantityDecompositionService:
    """Decomposes a base quantity into packaging units using LARGEST_FIRST strategy.

    Does NOT create physical boxes, pallets, or stock.
    """

    def __init__(self, db: Session):
        self.db = db
        self.resolver = ConversionPathResolver(db)

    def decompose(
        self,
        product_id: UUID,
        quantity: Decimal,
        source_unit_code: str = "UND",
        strategy: str = "LARGEST_FIRST",
    ) -> Dict[str, Any]:
        if quantity <= Decimal("0"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than zero.")

        # 1. Fetch product unit configuration & base unit
        stmt_config = select(ProductUnitConfigurationModel).where(ProductUnitConfigurationModel.product_id == product_id)
        config = self.db.scalar(stmt_config)

        if not config:
            # Fallback: check product.base_unit_code
            product = self.db.get(ProductModel, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
            stmt_base = select(UnitOfMeasureModel).where(UnitOfMeasureModel.normalized_code == product.base_unit_code.upper())
            base_unit = self.db.scalar(stmt_base)
            if not base_unit:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Base unit of measure not found.")
        else:
            base_unit = config.base_unit

        # 2. Fetch packaging definitions ordered by level_order DESC (largest packaging unit first)
        stmt_pkg = select(ProductPackagingDefinitionModel).where(
            ProductPackagingDefinitionModel.product_id == product_id,
            ProductPackagingDefinitionModel.status == "ACTIVE",
        ).order_by(ProductPackagingDefinitionModel.level_order.desc())

        pkgs = list(self.db.scalars(stmt_pkg).all())

        # Normalize quantity to base unit
        stmt_src = select(UnitOfMeasureModel).where(UnitOfMeasureModel.normalized_code == source_unit_code.upper())
        src_unit = self.db.scalar(stmt_src)
        if not src_unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source unit '{source_unit_code}' not found.")

        factor_to_base, _, _ = self.resolver.resolve_path(
            source_unit_id=src_unit.id,
            target_unit_id=base_unit.id,
            product_id=product_id,
        )
        base_qty = quantity * factor_to_base

        components = []
        remaining = base_qty

        for pkg in pkgs:
            # Calculate how many base units 1 packaging_unit represents
            pkg_factor_to_base, _, _ = self.resolver.resolve_path(
                source_unit_id=pkg.packaging_unit_id,
                target_unit_id=base_unit.id,
                product_id=product_id,
            )

            if remaining >= pkg_factor_to_base and pkg_factor_to_base > Decimal("0"):
                count_units = int(remaining // pkg_factor_to_base)
                if count_units > 0:
                    components.append({
                        "unit_code": pkg.packaging_unit.code,
                        "unit_name": pkg.packaging_unit.name,
                        "quantity": str(count_units),
                        "equivalent_base_quantity": str(Decimal(count_units) * pkg_factor_to_base),
                    })
                    remaining -= Decimal(count_units) * pkg_factor_to_base

        if remaining > Decimal("0"):
            clean_rem = remaining.normalize()
            components.append({
                "unit_code": base_unit.code,
                "unit_name": base_unit.name,
                "quantity": str(clean_rem),
                "equivalent_base_quantity": str(clean_rem),
            })

        return {
            "input_quantity": str(quantity),
            "input_unit": source_unit_code,
            "normalized_base_quantity": str(base_qty),
            "base_unit_code": base_unit.code,
            "components": components,
            "residual": str(remaining) if remaining != Decimal("0") else "0",
            "strategy": strategy,
            "decomposed_at": self.db.execute(select(func.now())).scalar().isoformat(),
        }
