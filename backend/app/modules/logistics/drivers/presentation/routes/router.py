"""FastAPI REST Router for Phase 029 — Driver Master Data."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.drivers.application.services.carrier_contact_photo_service import (
    DriverCarrierAssignmentService,
    DriverContactService,
    DriverPhotoService,
)
from app.modules.logistics.drivers.application.services.document_restriction_service import (
    DriverDocumentService,
    DriverOperationalRestrictionService,
)
from app.modules.logistics.drivers.application.services.driver_service import DriverService
from app.modules.logistics.drivers.application.services.identity_license_service import (
    DriverCategoryService,
    DriverIdentityService,
    DriverLicenseService,
)
from app.modules.logistics.drivers.domain.services.services import (
    DriverDuplicateDetectionService,
    DriverExpirationAlertService,
    EvaluateDriverVehicleCompatibility,
)
from app.modules.logistics.drivers.presentation.schemas.dto import (
    AssignCarrierRequestDTO,
    AssignCategoryRequestDTO,
    CreateDriverContactRequestDTO,
    CreateDriverDocumentRequestDTO,
    CreateDriverIdentityDocumentRequestDTO,
    CreateDriverLicenseRequestDTO,
    CreateDriverRequestDTO,
    CreateDriverRestrictionRequestDTO,
    DriverBlockRequestDTO,
    DriverCarrierAssignmentResponseDTO,
    DriverContactResponseDTO,
    DriverDocumentResponseDTO,
    DriverIdentityDocumentResponseDTO,
    DriverLicenseCategoryAssignmentResponseDTO,
    DriverLicenseCategoryResponseDTO,
    DriverLicenseResponseDTO,
    DriverPhotoResponseDTO,
    DriverResponseDTO,
    DriverRestrictionResponseDTO,
    DriverSummaryDTO,
    DuplicateCheckRequestDTO,
    DuplicateCheckResponseDTO,
    LinkDriverPhotoRequestDTO,
    UpdateDriverRequestDTO,
    VehicleCompatibilityRequestDTO,
    VehicleCompatibilityResponseDTO,
)

router = APIRouter(prefix="", tags=["Drivers"])


def get_actor_id(x_actor_id: Optional[str] = Header(None)) -> UUID:
    if x_actor_id:
        return UUID(x_actor_id)
    return UUID("37432a2c-8420-4393-acab-c590a02b1987")


def get_org_id(x_org_id: Optional[str] = Header(None)) -> UUID:
    if x_org_id:
        return UUID(x_org_id)
    return UUID("f8545a6d-4183-478b-8be2-0df2867475a2")


# --- CATEGORIES (GLOBAL / SEED) ---
@router.post("/driver-license-categories/seed", response_model=List[DriverLicenseCategoryResponseDTO])
def seed_categories(db: Session = Depends(get_db)):
    service = DriverCategoryService(db)
    return service.seed_default_categories()


@router.get("/driver-license-categories", response_model=List[DriverLicenseCategoryResponseDTO])
def list_categories(
    country_code: str = Query("PE"),
    db: Session = Depends(get_db),
):
    service = DriverCategoryService(db)
    return service.list_categories(country_code=country_code)


# --- DRIVERS CRUD ---
@router.post("/drivers", response_model=DriverResponseDTO, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: CreateDriverRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverService(db)
    return service.create_driver(
        organization_id=org_id,
        first_name=payload.first_name,
        paternal_last_name=payload.paternal_last_name,
        middle_name=payload.middle_name,
        maternal_last_name=payload.maternal_last_name,
        custom_code=payload.custom_code,
        date_of_birth=payload.date_of_birth,
        nationality_country_code=payload.nationality_country_code,
        notes=payload.notes,
        actor_id=actor_id,
    )


@router.get("/drivers", response_model=List[DriverSummaryDTO])
def list_drivers(
    search: Optional[str] = Query(None),
    lifecycle_status: Optional[str] = Query(None),
    compliance_status: Optional[str] = Query(None),
    eligibility_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    service = DriverService(db)
    items, _ = service.list_drivers(
        organization_id=org_id,
        search=search,
        lifecycle_status=lifecycle_status,
        compliance_status=compliance_status,
        eligibility_status=eligibility_status,
        page=page,
        page_size=page_size,
    )
    return items


@router.get("/drivers/{driver_id}", response_model=DriverResponseDTO)
def get_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    service = DriverService(db)
    return service.get_driver(driver_id=driver_id, organization_id=org_id)


@router.patch("/drivers/{driver_id}", response_model=DriverResponseDTO)
def update_driver(
    driver_id: UUID,
    payload: UpdateDriverRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverService(db)
    return service.update_driver(
        driver_id=driver_id,
        organization_id=org_id,
        first_name=payload.first_name,
        paternal_last_name=payload.paternal_last_name,
        middle_name=payload.middle_name,
        maternal_last_name=payload.maternal_last_name,
        date_of_birth=payload.date_of_birth,
        notes=payload.notes,
        expected_row_version=payload.expected_row_version,
        actor_id=actor_id,
    )


@router.post("/drivers/{driver_id}/activate", response_model=DriverResponseDTO)
def activate_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverService(db)
    return service.activate_driver(driver_id=driver_id, organization_id=org_id, actor_id=actor_id)


@router.post("/drivers/{driver_id}/block", response_model=DriverResponseDTO)
def block_driver(
    driver_id: UUID,
    payload: DriverBlockRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverService(db)
    return service.block_driver(driver_id=driver_id, organization_id=org_id, reason=payload.reason, actor_id=actor_id)


@router.post("/drivers/{driver_id}/unblock", response_model=DriverResponseDTO)
def unblock_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverService(db)
    return service.unblock_driver(driver_id=driver_id, organization_id=org_id, actor_id=actor_id)


# --- IDENTITY DOCUMENTS ---
@router.post("/drivers/{driver_id}/identity-documents", response_model=DriverIdentityDocumentResponseDTO, status_code=status.HTTP_201_CREATED)
def add_identity_document(
    driver_id: UUID,
    payload: CreateDriverIdentityDocumentRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverIdentityService(db)
    return service.add_identity_document(
        driver_id=driver_id,
        organization_id=org_id,
        document_type=payload.document_type,
        value=payload.value,
        country_code=payload.country_code,
        is_primary=payload.is_primary,
        issued_at=payload.issued_at,
        expires_at=payload.expires_at,
        valid_from=payload.valid_from,
        actor_id=actor_id,
    )


# --- LICENSES & CATEGORIES ---
@router.post("/drivers/{driver_id}/licenses", response_model=DriverLicenseResponseDTO, status_code=status.HTTP_201_CREATED)
def add_license(
    driver_id: UUID,
    payload: CreateDriverLicenseRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverLicenseService(db)
    return service.add_license(
        driver_id=driver_id,
        organization_id=org_id,
        license_number=payload.license_number,
        expires_at=payload.expires_at,
        issuing_authority=payload.issuing_authority,
        country_code=payload.country_code,
        valid_from=payload.valid_from,
        primary_license=payload.primary_license,
        notes=payload.notes,
        actor_id=actor_id,
    )


@router.post("/driver-licenses/{license_id}/categories", response_model=DriverLicenseCategoryAssignmentResponseDTO, status_code=status.HTTP_201_CREATED)
def assign_category(
    license_id: UUID,
    payload: AssignCategoryRequestDTO,
    db: Session = Depends(get_db),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverLicenseService(db)
    return service.assign_category(
        license_id=license_id,
        category_code=payload.category_code,
        expires_at=payload.expires_at,
        country_code=payload.country_code,
        valid_from=payload.valid_from,
        actor_id=actor_id,
    )


# --- CARRIER ASSIGNMENTS ---
@router.post("/drivers/{driver_id}/carrier-assignments", response_model=DriverCarrierAssignmentResponseDTO, status_code=status.HTTP_201_CREATED)
def assign_carrier(
    driver_id: UUID,
    payload: AssignCarrierRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverCarrierAssignmentService(db)
    return service.assign_carrier(
        driver_id=driver_id,
        organization_id=org_id,
        carrier_business_partner_id=payload.carrier_business_partner_id,
        assignment_type=payload.assignment_type,
        valid_from=payload.valid_from,
        employment_reference=payload.employment_reference,
        actor_id=actor_id,
    )


# --- CONTACTS & PHOTOS ---
@router.post("/drivers/{driver_id}/contacts", response_model=DriverContactResponseDTO, status_code=status.HTTP_201_CREATED)
def add_contact(
    driver_id: UUID,
    payload: CreateDriverContactRequestDTO,
    db: Session = Depends(get_db),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverContactService(db)
    return service.add_contact(
        driver_id=driver_id,
        contact_type=payload.contact_type,
        phone=payload.phone,
        mobile_phone=payload.mobile_phone,
        email=payload.email,
        address_line=payload.address_line,
        district=payload.district,
        province=payload.province,
        department=payload.department,
        is_primary=payload.is_primary,
        actor_id=actor_id,
    )


@router.post("/drivers/{driver_id}/photos", response_model=DriverPhotoResponseDTO, status_code=status.HTTP_201_CREATED)
def link_photo(
    driver_id: UUID,
    payload: LinkDriverPhotoRequestDTO,
    db: Session = Depends(get_db),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverPhotoService(db)
    return service.link_photo(
        driver_id=driver_id,
        file_reference_id=payload.file_reference_id,
        photo_type=payload.photo_type,
        source_type=payload.source_type,
        consent_reference=payload.consent_reference,
        actor_id=actor_id,
    )


# --- DOCUMENTS & RESTRICTIONS ---
@router.post("/drivers/{driver_id}/documents", response_model=DriverDocumentResponseDTO, status_code=status.HTTP_201_CREATED)
def add_document(
    driver_id: UUID,
    payload: CreateDriverDocumentRequestDTO,
    db: Session = Depends(get_db),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverDocumentService(db)
    return service.add_document(
        driver_id=driver_id,
        document_type=payload.document_type,
        document_number=payload.document_number,
        issuer=payload.issuer,
        issued_at=payload.issued_at,
        valid_from=payload.valid_from,
        expires_at=payload.expires_at,
        file_reference_id=payload.file_reference_id,
        notes=payload.notes,
        actor_id=actor_id,
    )


@router.post("/drivers/{driver_id}/restrictions", response_model=DriverRestrictionResponseDTO, status_code=status.HTTP_201_CREATED)
def add_restriction(
    driver_id: UUID,
    payload: CreateDriverRestrictionRequestDTO,
    db: Session = Depends(get_db),
    actor_id: UUID = Depends(get_actor_id),
):
    service = DriverOperationalRestrictionService(db)
    return service.add_restriction(
        driver_id=driver_id,
        restriction_type=payload.restriction_type,
        description=payload.description,
        reason=payload.reason,
        severity=payload.severity,
        blocking=payload.blocking,
        valid_until=payload.valid_until,
        actor_id=actor_id,
    )


# --- UTILITIES (COMPATIBILITY, DUPLICATES, ALERTS) ---
@router.post("/drivers/{driver_id}/vehicle-compatibility", response_model=VehicleCompatibilityResponseDTO)
def evaluate_vehicle_compatibility(
    driver_id: UUID,
    payload: VehicleCompatibilityRequestDTO,
    db: Session = Depends(get_db),
):
    return EvaluateDriverVehicleCompatibility.evaluate(
        db=db,
        driver_id=driver_id,
        vehicle_type=payload.vehicle_type,
        body_type=payload.body_type,
        effective_at=payload.effective_at,
    )


@router.post("/drivers/duplicate-check", response_model=DuplicateCheckResponseDTO)
def check_duplicates(
    payload: DuplicateCheckRequestDTO,
    db: Session = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
):
    return DriverDuplicateDetectionService.check_duplicates(
        db=db,
        organization_id=org_id,
        identity_document_value=payload.identity_document_value,
        license_number=payload.license_number,
        first_name=payload.first_name,
        paternal_last_name=payload.paternal_last_name,
        phone=payload.phone,
    )


@router.get("/drivers/{driver_id}/alerts")
def get_driver_alerts(
    driver_id: UUID,
    db: Session = Depends(get_db),
):
    return DriverExpirationAlertService.get_driver_alerts(db=db, driver_id=driver_id)
