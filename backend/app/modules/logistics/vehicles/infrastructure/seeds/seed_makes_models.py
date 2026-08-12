"""Seed standard vehicle makes and models into vehicle_makes and vehicle_models."""

from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.logistics.vehicles.infrastructure.persistence.models import VehicleMakeModel, VehicleModelModel


SYSTEM_MAKES_AND_MODELS = [
    ("VOLVO", "Volvo Trucks", "SE", [("FH540", "TRACTOR_TRUCK"), ("FM460", "HEAVY_TRUCK"), ("FMX", "HEAVY_TRUCK")]),
    ("SCANIA", "Scania", "SE", [("R500", "TRACTOR_TRUCK"), ("G450", "HEAVY_TRUCK"), ("P360", "LIGHT_TRUCK")]),
    ("MERCEDES", "Mercedes-Benz Trucks", "DE", [("ACTROS", "TRACTOR_TRUCK"), ("ATEGO", "MEDIUM_TRUCK"), ("SPRINTER", "VAN")]),
    ("ISUZU", "Isuzu Motors", "JP", [("NPR", "LIGHT_TRUCK"), ("FVR", "MEDIUM_TRUCK"), ("CYZ", "HEAVY_TRUCK")]),
    ("HYUNDAI", "Hyundai Commercial", "KR", [("H100", "PANEL_VAN"), ("HD78", "LIGHT_TRUCK"), ("XCIENT", "TRACTOR_TRUCK")]),
    ("TOYOTA", "Toyota", "JP", [("HILUX", "PICKUP"), ("HIACE", "VAN")]),
]


def seed_system_vehicle_makes_and_models(db: Session):
    for code, name, country, models_list in SYSTEM_MAKES_AND_MODELS:
        norm_make = name.strip().upper()
        make = db.scalars(
            select(VehicleMakeModel).where(VehicleMakeModel.normalized_name == norm_make)
        ).first()

        if not make:
            make = VehicleMakeModel(
                id=uuid4(),
                code=code,
                name=name,
                normalized_name=norm_make,
                country_code=country,
                status="ACTIVE",
                system_defined=True,
            )
            db.add(make)
            db.commit()
            db.refresh(make)

        for m_code, v_type in models_list:
            norm_mod = m_code.strip().upper()
            mod = db.scalars(
                select(VehicleModelModel).where(
                    VehicleModelModel.make_id == make.id,
                    VehicleModelModel.normalized_name == norm_mod,
                )
            ).first()

            if not mod:
                mod = VehicleModelModel(
                    id=uuid4(),
                    make_id=make.id,
                    code=m_code,
                    name=m_code,
                    normalized_name=norm_mod,
                    vehicle_type=v_type,
                    status="ACTIVE",
                    system_defined=True,
                )
                db.add(mod)
                db.commit()
