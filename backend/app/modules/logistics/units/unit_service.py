"""Unit catalog and configuration application service for Phase 024."""

import hashlib
import json
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.logistics.units.models import (
    MeasurementDimensionModel,
    ProductPackagingDefinitionModel,
    ProductUnitConfigurationModel,
    UnitConversionRuleModel,
    UnitOfMeasureModel,
    UnitOfMeasureVersionModel,
)
from app.modules.logistics.units.packaging_validator import ProductPackagingHierarchyValidator


class UnitCatalogService:
    def __init__(self, db: Session):
        self.db = db

    def list_dimensions(self) -> List[MeasurementDimensionModel]:
        stmt = select(MeasurementDimensionModel).order_by(MeasurementDimensionModel.code)
        return list(self.db.scalars(stmt).all())

    def list_units(
        self,
        dimension_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[UnitOfMeasureModel]:
        stmt = select(UnitOfMeasureModel)
        if dimension_id:
            stmt = stmt.where(UnitOfMeasureModel.dimension_id == dimension_id)
        if organization_id:
            stmt = stmt.where(
                (UnitOfMeasureModel.organization_id == None) | (UnitOfMeasureModel.organization_id == organization_id)
            )
        else:
            stmt = stmt.where(UnitOfMeasureModel.organization_id == None)

        stmt = stmt.order_by(UnitOfMeasureModel.code)
        return list(self.db.scalars(stmt).all())

    def create_unit(
        self,
        dimension_id: UUID,
        code: str,
        name: str,
        symbol: str,
        unit_kind: str = "DERIVED",
        organization_id: Optional[UUID] = None,
        plural_name: Optional[str] = None,
        decimal_precision: int = 4,
        integer_only: bool = False,
        user_id: Optional[UUID] = None,
    ) -> UnitOfMeasureModel:
        norm_code = code.strip().upper()
        # Uniqueness check
        stmt = select(UnitOfMeasureModel).where(
            UnitOfMeasureModel.organization_id == organization_id,
            UnitOfMeasureModel.normalized_code == norm_code,
        )
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Unit code '{norm_code}' already exists.",
            )

        dimension = self.db.get(MeasurementDimensionModel, dimension_id)
        if not dimension:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement dimension not found.")

        unit_scope = "ORGANIZATION" if organization_id else "SYSTEM"

        unit = UnitOfMeasureModel(
            organization_id=organization_id,
            dimension_id=dimension_id,
            code=code.strip(),
            normalized_code=norm_code,
            name=name.strip(),
            plural_name=plural_name,
            symbol=symbol.strip(),
            unit_scope=unit_scope,
            unit_kind=unit_kind,
            decimal_precision=decimal_precision,
            integer_only=integer_only,
            status="ACTIVE",
            system_defined=False if organization_id else True,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def create_conversion_rule(
        self,
        source_unit_id: UUID,
        target_unit_id: UUID,
        multiplier: Decimal,
        organization_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        allows_inverse: bool = True,
        rounding_policy: str = "HALF_UP",
        user_id: Optional[UUID] = None,
    ) -> UnitConversionRuleModel:
        if multiplier <= Decimal("0"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Multiplier must be greater than zero.")

        if source_unit_id == target_unit_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and target units must be different.")

        src = self.db.get(UnitOfMeasureModel, source_unit_id)
        tgt = self.db.get(UnitOfMeasureModel, target_unit_id)

        if not src or not tgt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target unit not found.")

        scope = "PRODUCT" if product_id else ("ORGANIZATION" if organization_id else "SYSTEM")

        c_hash = hashlib.sha256(
            f"{scope}:{product_id}:{source_unit_id}:{target_unit_id}:{multiplier}".encode("utf-8")
        ).hexdigest()

        rule = UnitConversionRuleModel(
            organization_id=organization_id,
            product_id=product_id,
            source_unit_id=source_unit_id,
            target_unit_id=target_unit_id,
            conversion_scope=scope,
            multiplier=multiplier,
            allows_inverse=allows_inverse,
            rounding_policy=rounding_policy,
            status="ACTIVE",
            content_hash=c_hash,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def configure_product_units(
        self,
        product_id: UUID,
        base_unit_id: UUID,
        purchase_unit_id: Optional[UUID] = None,
        reception_unit_id: Optional[UUID] = None,
        storage_unit_id: Optional[UUID] = None,
        picking_unit_id: Optional[UUID] = None,
        dispatch_unit_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductUnitConfigurationModel:
        stmt = select(ProductUnitConfigurationModel).where(ProductUnitConfigurationModel.product_id == product_id)
        config = self.db.scalar(stmt)

        if not config:
            config = ProductUnitConfigurationModel(
                product_id=product_id,
                base_unit_id=base_unit_id,
                purchase_unit_id=purchase_unit_id,
                reception_unit_id=reception_unit_id,
                storage_unit_id=storage_unit_id,
                picking_unit_id=picking_unit_id,
                dispatch_unit_id=dispatch_unit_id,
                status="ACTIVE",
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(config)
        else:
            config.base_unit_id = base_unit_id
            config.purchase_unit_id = purchase_unit_id
            config.reception_unit_id = reception_unit_id
            config.storage_unit_id = storage_unit_id
            config.picking_unit_id = picking_unit_id
            config.dispatch_unit_id = dispatch_unit_id
            config.updated_by = user_id

        self.db.commit()
        self.db.refresh(config)
        return config

    def add_product_packaging(
        self,
        product_id: UUID,
        packaging_unit_id: UUID,
        contained_unit_id: UUID,
        contained_quantity: Decimal,
        level_order: int,
        package_type: str = "BOX",
        gross_weight: Optional[Decimal] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductPackagingDefinitionModel:
        ProductPackagingHierarchyValidator.validate_definitions([
            {
                "packaging_unit_id": str(packaging_unit_id),
                "contained_unit_id": str(contained_unit_id),
                "contained_quantity": contained_quantity,
            }
        ])

        stmt = select(ProductPackagingDefinitionModel).where(
            ProductPackagingDefinitionModel.product_id == product_id,
            ProductPackagingDefinitionModel.packaging_unit_id == packaging_unit_id,
        )
        pkg = self.db.scalar(stmt)

        if not pkg:
            pkg = ProductPackagingDefinitionModel(
                product_id=product_id,
                packaging_unit_id=packaging_unit_id,
                contained_unit_id=contained_unit_id,
                contained_quantity=contained_quantity,
                level_order=level_order,
                package_type=package_type,
                gross_weight=gross_weight,
                status="ACTIVE",
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(pkg)
        else:
            pkg.contained_unit_id = contained_unit_id
            pkg.contained_quantity = contained_quantity
            pkg.level_order = level_order
            pkg.package_type = package_type
            pkg.gross_weight = gross_weight
            pkg.updated_by = user_id

        self.db.commit()
        self.db.refresh(pkg)
        return pkg
