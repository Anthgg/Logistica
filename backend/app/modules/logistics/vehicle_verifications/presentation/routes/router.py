"""FastAPI REST Endpoints for Phase 028 — Vehicle Verifications."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.vehicle_verifications.application.services.apply_verification_service import ApplyVehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.assisted_verification_service import AssistedVehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.source_service import VehicleVerificationSourceService
from app.modules.logistics.vehicle_verifications.application.services.verification_service import VehicleVerificationService
from app.modules.logistics.vehicle_verifications.presentation.schemas.dto import (
    ApplyVerificationFieldsRequestDTO,
    AssistedVerificationResponseDTO,
    CreateAssistedVerificationRequestDTO,
    CreateVehicleVerificationRequestDTO,
    VehicleVerificationComplianceResponseDTO,
    VehicleVerificationResponseDTO,
    VehicleVerificationSourceResponseDTO,
)

router = APIRouter(prefix="", tags=["Vehicle Verifications"])


# Mock actor & org helpers for development/testing
def get_actor_id(x_actor_id: Optional[str] = Header(None)) -> UUID:
    if x_actor_id:
        return UUID(x_actor_id)
    return UUID("37432a2c-8420-4393-acab-c590a02b1987")


def get_org_id(x_org_id: Optional[str] = Header(None)) -> UUID:
    if x_org_id:
        return UUID(x_org_id)
    return UUID("f8545a6d-4183-478b-8be2-0df2867475a2")


# --- SOURCES ---
@router.get("/vehicle-verification-sources", response_model=List[VehicleVerificationSourceResponseDTO])
def list_sources(
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    service = VehicleVerificationSourceService(db)
    return service.list_sources(enabled_only=enabled_only)


@router.post("/vehicle-verification-sources/seed", response_model=List[VehicleVerificationSourceResponseDTO])
def seed_sources(db: Session = Depends(get_db)):
    service = VehicleVerificationSourceService(db)
    return service.seed_default_sources()


# --- VERIFICATIONS ---
@router.post("/vehicles/{vehicle_id}/verifications", response_model=VehicleVerificationResponseDTO, status_code=status.HTTP_201_CREATED)
def request_verification(
    vehicle_id: UUID,
    payload: CreateVehicleVerificationRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = VehicleVerificationService(db)
    return service.request_verification(
        organization_id=org_id,
        vehicle_id=vehicle_id,
        domain=payload.verification_domain,
        source_code=payload.source_code,
        actor_id=actor_id,
        purpose=payload.purpose,
        file_reference_id=payload.file_reference_id,
    )


@router.get("/vehicles/{vehicle_id}/verifications", response_model=List[VehicleVerificationResponseDTO])
def list_vehicle_verifications(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    service = VehicleVerificationService(db)
    return service.list_verifications(vehicle_id, org_id)


@router.get("/vehicles/{vehicle_id}/verification-compliance", response_model=VehicleVerificationComplianceResponseDTO)
def get_verification_compliance(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    service = VehicleVerificationService(db)
    return service.get_verification_compliance(vehicle_id, org_id)


# --- ASSISTED VERIFICATIONS ---
@router.post("/vehicles/{vehicle_id}/assisted-verifications", response_model=AssistedVerificationResponseDTO, status_code=status.HTTP_201_CREATED)
def create_assisted_verification(
    vehicle_id: UUID,
    payload: CreateAssistedVerificationRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = AssistedVehicleVerificationService(db)
    return service.create_assisted_verification(
        organization_id=org_id,
        vehicle_id=vehicle_id,
        domain=payload.verification_domain,
        source_id=payload.source_id,
        verification_reason=payload.verification_reason,
        observed_plate=payload.observed_plate,
        actor_id=actor_id,
        source_reference=payload.source_reference,
        observed_owner=payload.observed_owner,
        observed_make=payload.observed_make,
        observed_model=payload.observed_model,
        observed_year=payload.observed_year,
        observed_status=payload.observed_status,
        observed_expiration=payload.observed_expiration,
        observations=payload.observations,
        evidence_reference_id=payload.evidence_reference_id,
        result_status=payload.result_status,
    )


@router.post("/assisted-vehicle-verifications/{assisted_id}/approve", response_model=VehicleVerificationResponseDTO)
def approve_assisted_verification(
    assisted_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    approver_id: UUID = Depends(get_actor_id),
):
    service = AssistedVehicleVerificationService(db)
    return service.approve_assisted_verification(
        assisted_id=assisted_id,
        organization_id=org_id,
        approver_id=approver_id,
        enforce_separation_of_duties=False,  # default False in dev API endpoint unless configured
    )


# --- CONTROLLED APPLICATION TO VEHICLE ---
@router.post("/vehicle-verifications/{verification_id}/apply")
def apply_verified_fields(
    verification_id: UUID,
    payload: ApplyVerificationFieldsRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = ApplyVehicleVerificationService(db)
    ver = service.apply_verified_fields(
        verification_id=verification_id,
        organization_id=org_id,
        selected_fields=payload.selected_fields,
        reason=payload.reason,
        actor_id=actor_id,
    )
    return {"message": "Campos verificados aplicados exitosamente.", "new_version_id": str(ver.id), "version": ver.version}
