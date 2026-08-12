"""Vehicle Make and Model Management Service (Phase 027)."""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.logistics.vehicles.domain.errors.exceptions import (
    VehicleMakeNotFoundError,
    VehicleModelMakeMismatchError,
    VehicleModelNotFoundError,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleMakeModel,
    VehicleModelModel,
)


class VehicleMakeModelService:
    def __init__(self, db: Session):
        self.db = db

    def get_makes(self, organization_id: UUID) -> List[VehicleMakeModel]:
        return list(
            self.db.scalars(
                select(VehicleMakeModel).where(
                    and_(
                        or_(
                            VehicleMakeModel.system_defined.is_(True),
                            VehicleMakeModel.organization_id == organization_id,
                        ),
                        VehicleMakeModel.status == "ACTIVE",
                    )
                ).order_by(VehicleMakeModel.name)
            ).all()
        )

    def create_make(self, organization_id: UUID, name: str, code: str, country_code: Optional[str] = None, actor_id: Optional[UUID] = None) -> VehicleMakeModel:
        norm = name.strip().upper()
        existing = self.db.scalars(
            select(VehicleMakeModel).where(
                and_(
                    or_(VehicleMakeModel.system_defined.is_(True), VehicleMakeModel.organization_id == organization_id),
                    VehicleMakeModel.normalized_name == norm,
                )
            )
        ).first()

        if existing:
            return existing

        make = VehicleMakeModel(
            id=uuid4(),
            organization_id=organization_id,
            code=code.upper(),
            name=name,
            normalized_name=norm,
            country_code=country_code,
            status="ACTIVE",
            system_defined=False,
            created_by=actor_id,
        )
        self.db.add(make)
        self.db.commit()
        self.db.refresh(make)
        return make

    def get_models_by_make(self, make_id: UUID, organization_id: UUID) -> List[VehicleModelModel]:
        make = self.db.get(VehicleMakeModel, make_id)
        if not make:
            raise VehicleMakeNotFoundError(str(make_id))

        return list(
            self.db.scalars(
                select(VehicleModelModel).where(
                    and_(
                        VehicleModelModel.make_id == make_id,
                        or_(
                            VehicleModelModel.system_defined.is_(True),
                            VehicleModelModel.organization_id == organization_id,
                        ),
                        VehicleModelModel.status == "ACTIVE",
                    )
                ).order_by(VehicleModelModel.name)
            ).all()
        )

    def create_model(
        self,
        make_id: UUID,
        organization_id: UUID,
        name: str,
        code: str,
        vehicle_type: Optional[str] = None,
        body_type: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> VehicleModelModel:
        make = self.db.get(VehicleMakeModel, make_id)
        if not make:
            raise VehicleMakeNotFoundError(str(make_id))

        norm = name.strip().upper()
        existing = self.db.scalars(
            select(VehicleModelModel).where(
                and_(
                    VehicleModelModel.make_id == make_id,
                    or_(VehicleModelModel.system_defined.is_(True), VehicleModelModel.organization_id == organization_id),
                    VehicleModelModel.normalized_name == norm,
                )
            )
        ).first()

        if existing:
            return existing

        model = VehicleModelModel(
            id=uuid4(),
            make_id=make_id,
            organization_id=organization_id,
            code=code.upper(),
            name=name,
            normalized_name=norm,
            vehicle_type=vehicle_type,
            body_type=body_type,
            status="ACTIVE",
            system_defined=False,
            created_by=actor_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
