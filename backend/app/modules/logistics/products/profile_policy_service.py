"""Physical profile, tracking policy, and conditions service for Phase 023."""

from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.products.models import (
    ProductHandlingConditionModel,
    ProductModel,
    ProductPhysicalProfileModel,
    ProductStorageConditionModel,
    ProductTrackingPolicyModel,
)
from app.modules.logistics.products.volume_calculator import ProductVolumeCalculator


class ProductProfileAndPolicyService:
    def __init__(self, db: Session):
        self.db = db

    def update_physical_profile(
        self,
        product_id: UUID,
        net_weight_value: Optional[Decimal] = None,
        net_weight_unit: Optional[str] = "KG",
        gross_weight_value: Optional[Decimal] = None,
        gross_weight_unit: Optional[str] = "KG",
        length_value: Optional[Decimal] = None,
        width_value: Optional[Decimal] = None,
        height_value: Optional[Decimal] = None,
        dimension_unit: Optional[str] = "CM",
        reported_volume_value: Optional[Decimal] = None,
        volume_unit: Optional[str] = "M3",
        measurement_source: str = "MANUAL",
        user_id: Optional[UUID] = None,
    ) -> ProductPhysicalProfileModel:
        product = self.db.get(ProductModel, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        # Physical checks
        if net_weight_value is not None and gross_weight_value is not None:
            if gross_weight_value < net_weight_value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gross weight cannot be less than net weight.",
                )

        # Calculate volume
        calc_res = ProductVolumeCalculator.calculate_volume(length_value, width_value, height_value, dimension_unit)
        calc_vol = calc_res.get("calculated_value")
        final_vol = reported_volume_value if reported_volume_value is not None else calc_vol
        final_vol_unit = volume_unit if reported_volume_value is not None else calc_res.get("calculated_unit")

        stmt = select(ProductPhysicalProfileModel).where(ProductPhysicalProfileModel.product_id == product_id)
        profile = self.db.scalar(stmt)

        if not profile:
            profile = ProductPhysicalProfileModel(
                product_id=product_id,
                net_weight_value=net_weight_value,
                net_weight_unit=net_weight_unit,
                gross_weight_value=gross_weight_value,
                gross_weight_unit=gross_weight_unit,
                length_value=length_value,
                width_value=width_value,
                height_value=height_value,
                dimension_unit=dimension_unit,
                volume_value=final_vol,
                volume_unit=final_vol_unit,
                measurement_source=measurement_source,
                status="ACTIVE",
            )
            self.db.add(profile)
        else:
            profile.net_weight_value = net_weight_value
            profile.net_weight_unit = net_weight_unit
            profile.gross_weight_value = gross_weight_value
            profile.gross_weight_unit = gross_weight_unit
            profile.length_value = length_value
            profile.width_value = width_value
            profile.height_value = height_value
            profile.dimension_unit = dimension_unit
            profile.volume_value = final_vol
            profile.volume_unit = final_vol_unit
            profile.measurement_source = measurement_source

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_tracking_policy(
        self,
        product_id: UUID,
        tracking_type: str = "NONE",
        lot_control: bool = False,
        serial_control: bool = False,
        expiration_control: str = "NONE",
        manufacturing_date_control: bool = False,
        best_before_control: bool = False,
        minimum_shelf_life_days: Optional[int] = None,
        total_shelf_life_days: Optional[int] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductTrackingPolicyModel:
        product = self.db.get(ProductModel, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        # Validation rules
        if tracking_type == "SERIAL" and not serial_control:
            serial_control = True
        if tracking_type in ["LOT", "LOT_AND_SERIAL"]:
            lot_control = True

        if expiration_control == "REQUIRED" and total_shelf_life_days is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total shelf life in days is required when expiration control is REQUIRED.",
            )

        if minimum_shelf_life_days is not None and total_shelf_life_days is not None:
            if minimum_shelf_life_days > total_shelf_life_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Minimum shelf life cannot exceed total shelf life.",
                )

        stmt = select(ProductTrackingPolicyModel).where(ProductTrackingPolicyModel.product_id == product_id)
        policy = self.db.scalar(stmt)

        if not policy:
            policy = ProductTrackingPolicyModel(
                product_id=product_id,
                tracking_type=tracking_type,
                lot_control=lot_control,
                serial_control=serial_control,
                expiration_control=expiration_control,
                manufacturing_date_control=manufacturing_date_control,
                best_before_control=best_before_control,
                minimum_shelf_life_days=minimum_shelf_life_days,
                total_shelf_life_days=total_shelf_life_days,
                status="ACTIVE",
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(policy)
        else:
            policy.tracking_type = tracking_type
            policy.lot_control = lot_control
            policy.serial_control = serial_control
            policy.expiration_control = expiration_control
            policy.manufacturing_date_control = manufacturing_date_control
            policy.best_before_control = best_before_control
            policy.minimum_shelf_life_days = minimum_shelf_life_days
            policy.total_shelf_life_days = total_shelf_life_days
            policy.updated_by = user_id

        self.db.commit()
        self.db.refresh(policy)
        return policy

    def add_storage_condition(
        self,
        product_id: UUID,
        condition_type: str,
        minimum_value: Optional[Decimal] = None,
        maximum_value: Optional[Decimal] = None,
        unit_code: Optional[str] = None,
        severity: str = "HARD_BLOCK",
        handling_instruction: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> ProductStorageConditionModel:
        if minimum_value is not None and maximum_value is not None:
            if minimum_value > maximum_value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum value cannot be greater than maximum value.")

        sc = ProductStorageConditionModel(
            product_id=product_id,
            condition_type=condition_type.upper(),
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            unit_code=unit_code.upper() if unit_code else None,
            severity=severity,
            handling_instruction=handling_instruction,
            status="ACTIVE",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(sc)
        self.db.commit()
        self.db.refresh(sc)
        return sc
