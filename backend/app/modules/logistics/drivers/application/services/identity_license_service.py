"""Services for Identity Documents, Driver Licenses, Categories and Category Assignments."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.drivers.domain.errors.exceptions import (
    DriverIdentityDocumentConflict,
    DriverIdentityDocumentNotFound,
    DriverLicenseCategoryMissing,
    DriverLicenseConflict,
    DriverLicenseNotFound,
    DriverNotFound,
)
from app.modules.logistics.drivers.domain.services.services import (
    DriverIdentityDocumentNormalizer,
    DriverLicenseNormalizer,
)
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverIdentityDocumentModel,
    DriverLicenseCategoryAssignmentModel,
    DriverLicenseCategoryModel,
    DriverLicenseModel,
    DriverLicenseRestrictionModel,
    DriverModel,
)


class DriverIdentityService:
    def __init__(self, db: Session):
        self.db = db

    def add_identity_document(
        self,
        driver_id: UUID,
        organization_id: UUID,
        document_type: str,
        value: str,
        country_code: str = "PE",
        is_primary: bool = True,
        issued_at: Optional[date] = None,
        expires_at: Optional[date] = None,
        valid_from: Optional[date] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverIdentityDocumentModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        norm_val = DriverIdentityDocumentNormalizer.normalize(document_type, value)
        masked_val = DriverIdentityDocumentNormalizer.mask(norm_val)

        # Check conflict
        existing = self.db.scalar(
            select(DriverIdentityDocumentModel.id).where(
                DriverIdentityDocumentModel.organization_id == organization_id,
                DriverIdentityDocumentModel.document_type == document_type,
                DriverIdentityDocumentModel.normalized_value == norm_val,
                DriverIdentityDocumentModel.status == "ACTIVE",
            )
        )
        if existing:
            raise DriverIdentityDocumentConflict(document_type, norm_val)

        if is_primary:
            # Demote existing primary
            existing_primaries = self.db.scalars(
                select(DriverIdentityDocumentModel).where(
                    DriverIdentityDocumentModel.driver_id == driver_id,
                    DriverIdentityDocumentModel.is_primary == True,
                )
            ).all()
            for ep in existing_primaries:
                ep.is_primary = False

        doc = DriverIdentityDocumentModel(
            organization_id=organization_id,
            driver_id=driver_id,
            document_type=document_type,
            country_code=country_code.upper(),
            value=norm_val,
            normalized_value=norm_val,
            masked_value=masked_val,
            is_primary=is_primary,
            verification_status="FORMAT_VALID",
            issued_at=issued_at,
            expires_at=expires_at,
            valid_from=valid_from or date.today(),
            status="ACTIVE",
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(doc)
        self.db.flush()

        if is_primary:
            driver.primary_identity_document_id = doc.id

        self.db.commit()
        self.db.refresh(doc)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.identity_document_created",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="DriverIdentityDocument",
                resource_id=str(doc.id),
                metadata={"driver_id": str(driver_id), "type": document_type, "masked": masked_val},
            ),
        )

        return doc


class DriverLicenseService:
    def __init__(self, db: Session):
        self.db = db

    def add_license(
        self,
        driver_id: UUID,
        organization_id: UUID,
        license_number: str,
        expires_at: date,
        issuing_authority: str = "MTC",
        country_code: str = "PE",
        valid_from: Optional[date] = None,
        primary_license: bool = True,
        notes: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverLicenseModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        norm_num = DriverLicenseNormalizer.normalize(license_number)
        masked_num = DriverLicenseNormalizer.mask(norm_num)

        # Check duplicate
        existing = self.db.scalar(
            select(DriverLicenseModel.id).where(
                DriverLicenseModel.organization_id == organization_id,
                DriverLicenseModel.issuing_authority == issuing_authority,
                DriverLicenseModel.normalized_license_number == norm_num,
                DriverLicenseModel.status.in_(["DRAFT", "ACTIVE"]),
            )
        )
        if existing:
            raise DriverLicenseConflict(norm_num)

        if primary_license:
            existing_primaries = self.db.scalars(
                select(DriverLicenseModel).where(
                    DriverLicenseModel.driver_id == driver_id,
                    DriverLicenseModel.primary_license == True,
                )
            ).all()
            for ep in existing_primaries:
                ep.primary_license = False

        license_obj = DriverLicenseModel(
            organization_id=organization_id,
            driver_id=driver_id,
            country_code=country_code.upper(),
            issuing_authority=issuing_authority.upper(),
            license_number=norm_num,
            normalized_license_number=norm_num,
            masked_license_number=masked_num,
            status="ACTIVE",
            verification_status="FORMAT_VALID",
            valid_from=valid_from or date.today(),
            expires_at=expires_at,
            primary_license=primary_license,
            notes=notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(license_obj)
        self.db.flush()

        if primary_license:
            driver.primary_license_id = license_obj.id

        self.db.commit()
        self.db.refresh(license_obj)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.license_created",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="DriverLicense",
                resource_id=str(license_obj.id),
                metadata={"driver_id": str(driver_id), "masked_num": masked_num},
            ),
        )

        return license_obj

    def assign_category(
        self,
        license_id: UUID,
        category_code: str,
        expires_at: date,
        country_code: str = "PE",
        valid_from: Optional[date] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverLicenseCategoryAssignmentModel:
        license_obj = self.db.get(DriverLicenseModel, license_id)
        if not license_obj:
            raise DriverLicenseNotFound(str(license_id))

        norm_cat = category_code.strip().upper()
        cat = self.db.scalar(
            select(DriverLicenseCategoryModel).where(
                DriverLicenseCategoryModel.country_code == country_code,
                DriverLicenseCategoryModel.normalized_code == norm_cat,
                DriverLicenseCategoryModel.status == "ACTIVE",
            )
        )
        if not cat:
            raise DriverLicenseCategoryMissing(norm_cat)

        assign = DriverLicenseCategoryAssignmentModel(
            driver_license_id=license_id,
            category_id=cat.id,
            status="ACTIVE",
            valid_from=valid_from or date.today(),
            expires_at=expires_at,
            created_by=actor_id,
        )
        self.db.add(assign)
        self.db.commit()
        self.db.refresh(assign)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.license_category_assigned",
                actor_user_id=actor_id,
                organization_id=license_obj.organization_id,
                resource_type="DriverLicenseCategoryAssignment",
                resource_id=str(assign.id),
                metadata={"license_id": str(license_id), "category": norm_cat},
            ),
        )

        return assign

    def add_license_restriction(
        self,
        license_id: UUID,
        restriction_code: str,
        description: str,
        severity: str = "MEDIUM",
        blocking: bool = False,
        expires_at: Optional[date] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverLicenseRestrictionModel:
        license_obj = self.db.get(DriverLicenseModel, license_id)
        if not license_obj:
            raise DriverLicenseNotFound(str(license_id))

        rest = DriverLicenseRestrictionModel(
            driver_license_id=license_id,
            restriction_code=restriction_code.upper(),
            restriction_type="LICENSE_ANNOTATION",
            description=description,
            severity=severity,
            blocking=blocking,
            valid_from=date.today(),
            expires_at=expires_at,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(rest)
        self.db.commit()
        self.db.refresh(rest)

        return rest


class DriverCategoryService:
    def __init__(self, db: Session):
        self.db = db

    def seed_default_categories(self) -> List[DriverLicenseCategoryModel]:
        defaults = [
            {"code": "A-I", "name": "Licencia Particular A-I", "hierarchy_level": 1},
            {"code": "A-IIa", "name": "Licencia Profesional A-IIa (Taxi/Emergencia)", "hierarchy_level": 2},
            {"code": "A-IIb", "name": "Licencia Profesional A-IIb (Cúster/Camión Ligero)", "hierarchy_level": 3},
            {"code": "A-IIIa", "name": "Licencia Profesional A-IIIa (Ómnibus)", "hierarchy_level": 4},
            {"code": "A-IIIb", "name": "Licencia Profesional A-IIIb (Camión Pesado/Remolque)", "hierarchy_level": 4},
            {"code": "A-IIIc", "name": "Licencia Profesional A-IIIc (Especializada/Tractor)", "hierarchy_level": 5},
        ]

        created = []
        today = date.today()
        for d in defaults:
            norm = d["code"].upper().strip()
            existing = self.db.scalar(
                select(DriverLicenseCategoryModel).where(
                    DriverLicenseCategoryModel.country_code == "PE",
                    DriverLicenseCategoryModel.normalized_code == norm,
                )
            )
            if not existing:
                cat = DriverLicenseCategoryModel(
                    country_code="PE",
                    code=d["code"],
                    normalized_code=norm,
                    name=d["name"],
                    hierarchy_level=d["hierarchy_level"],
                    status="ACTIVE",
                    system_defined=True,
                    effective_from=today,
                )
                self.db.add(cat)
                created.append(cat)
        self.db.commit()
        return created

    def list_categories(self, country_code: str = "PE") -> List[DriverLicenseCategoryModel]:
        return list(
            self.db.scalars(
                select(DriverLicenseCategoryModel).where(
                    DriverLicenseCategoryModel.country_code == country_code,
                    DriverLicenseCategoryModel.status == "ACTIVE",
                ).order_by(DriverLicenseCategoryModel.hierarchy_level.asc())
            ).all()
        )
