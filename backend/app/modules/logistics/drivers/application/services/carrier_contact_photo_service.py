"""Services for Carrier Assignments, Driver Contacts, Emergency Contacts and Photos."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.partners.models import BusinessPartnerModel, BusinessPartnerRoleModel
from app.modules.logistics.drivers.domain.errors.exceptions import (
    DriverCarrierBlockedError,
    DriverCarrierInvalid,
    DriverCarrierRoleRequired,
    DriverContactInvalid,
    DriverNotFound,
    DriverPhotoNotFound,
)
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverCarrierAssignmentModel,
    DriverContactModel,
    DriverEmergencyContactModel,
    DriverModel,
    DriverPhotoModel,
)


class DriverCarrierAssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def assign_carrier(
        self,
        driver_id: UUID,
        organization_id: UUID,
        carrier_business_partner_id: UUID,
        assignment_type: str = "INTERNAL",
        valid_from: Optional[date] = None,
        employment_reference: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverCarrierAssignmentModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        # Check partner
        partner = self.db.get(BusinessPartnerModel, carrier_business_partner_id)
        if not partner or partner.organization_id != organization_id:
            raise DriverCarrierInvalid("Socio comercial no encontrado o de otra organización.")
        if partner.lifecycle_status == "BLOCKED":
            raise DriverCarrierBlockedError(str(carrier_business_partner_id))

        # Check CARRIER role
        carrier_role = self.db.scalar(
            select(BusinessPartnerRoleModel).where(
                BusinessPartnerRoleModel.partner_id == carrier_business_partner_id,
                BusinessPartnerRoleModel.role_code == "CARRIER",
                BusinessPartnerRoleModel.status == "ACTIVE",
            )
        )
        if not carrier_role:
            raise DriverCarrierRoleRequired(str(carrier_business_partner_id))

        # End previous current assignments
        existing_currents = self.db.scalars(
            select(DriverCarrierAssignmentModel).where(
                DriverCarrierAssignmentModel.driver_id == driver_id,
                DriverCarrierAssignmentModel.status == "CURRENT",
            )
        ).all()
        for ca in existing_currents:
            ca.status = "SUPERSEDED"
            ca.valid_until = valid_from or date.today()
            ca.ended_by = actor_id
            ca.ended_at = utc_now()

        assign = DriverCarrierAssignmentModel(
            organization_id=organization_id,
            driver_id=driver_id,
            carrier_business_partner_id=carrier_business_partner_id,
            carrier_role_id=carrier_role.id,
            assignment_type=assignment_type,
            employment_reference=employment_reference,
            valid_from=valid_from or date.today(),
            status="CURRENT",
            created_by=actor_id,
        )
        self.db.add(assign)
        self.db.flush()

        driver.current_carrier_assignment_id = assign.id

        self.db.commit()
        self.db.refresh(assign)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.carrier_assigned",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="DriverCarrierAssignment",
                resource_id=str(assign.id),
                metadata={"driver_id": str(driver_id), "carrier_id": str(carrier_business_partner_id)},
            ),
        )

        return assign


class DriverContactService:
    def __init__(self, db: Session):
        self.db = db

    def add_contact(
        self,
        driver_id: UUID,
        contact_type: str = "PERSONAL",
        phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        email: Optional[str] = None,
        address_line: Optional[str] = None,
        district: Optional[str] = None,
        province: Optional[str] = None,
        department: Optional[str] = None,
        is_primary: bool = True,
        actor_id: Optional[UUID] = None,
    ) -> DriverContactModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        if not phone and not mobile_phone and not email:
            raise DriverContactInvalid("Debe proporcionar al menos un teléfono o correo electrónico.")

        if is_primary:
            existing_primaries = self.db.scalars(
                select(DriverContactModel).where(
                    DriverContactModel.driver_id == driver_id,
                    DriverContactModel.is_primary == True,
                )
            ).all()
            for ep in existing_primaries:
                ep.is_primary = False

        contact = DriverContactModel(
            driver_id=driver_id,
            contact_type=contact_type,
            email=email.strip().lower() if email else None,
            phone=phone.strip() if phone else None,
            mobile_phone=mobile_phone.strip() if mobile_phone else None,
            address_line=address_line.strip() if address_line else None,
            district=district.strip() if district else None,
            province=province.strip() if province else None,
            department=department.strip() if department else None,
            is_primary=is_primary,
            status="ACTIVE",
            valid_from=date.today(),
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(contact)
        self.db.flush()

        if is_primary:
            driver.primary_contact_id = contact.id

        self.db.commit()
        self.db.refresh(contact)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.contact_created",
                actor_user_id=actor_id,
                organization_id=driver.organization_id,
                resource_type="DriverContact",
                resource_id=str(contact.id),
                metadata={"driver_id": str(driver_id), "type": contact_type},
            ),
        )

        return contact


class DriverPhotoService:
    def __init__(self, db: Session):
        self.db = db

    def link_photo(
        self,
        driver_id: UUID,
        file_reference_id: UUID,
        photo_type: str = "PROFILE",
        source_type: str = "INTERNAL_CAPTURE",
        consent_reference: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverPhotoModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        # Deactivate current photos if profile
        if photo_type == "PROFILE":
            existing_currents = self.db.scalars(
                select(DriverPhotoModel).where(
                    DriverPhotoModel.driver_id == driver_id,
                    DriverPhotoModel.is_current == True,
                )
            ).all()
            for ep in existing_currents:
                ep.is_current = False
                ep.status = "REPLACED"

        photo = DriverPhotoModel(
            driver_id=driver_id,
            photo_type=photo_type,
            file_reference_id=file_reference_id,
            status="ACTIVE",
            is_current=True,
            captured_at=utc_now(),
            captured_by=actor_id,
            source_type=source_type,
            consent_reference=consent_reference,
        )
        self.db.add(photo)
        self.db.flush()

        if photo_type == "PROFILE":
            driver.current_photo_id = photo.id

        self.db.commit()
        self.db.refresh(photo)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.photo_linked",
                actor_user_id=actor_id,
                organization_id=driver.organization_id,
                resource_type="DriverPhoto",
                resource_id=str(photo.id),
                metadata={"driver_id": str(driver_id), "file_ref_id": str(file_reference_id)},
            ),
        )

        return photo
