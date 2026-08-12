"""Application service for Driver lifecycle and core CRUD operations."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.drivers.domain.errors.exceptions import (
    DriverBlockedError,
    DriverCannotBeActivated,
    DriverCannotBeRetired,
    DriverCodeConflict,
    DriverNotFound,
    DriverStatusInvalid,
    DriverVersionConflict,
)
from app.modules.logistics.drivers.domain.services.services import (
    DriverCodeService,
    DriverDocumentComplianceResolver,
    DriverOperationalEligibilityResolver,
    DriverSnapshotProvider,
)
from app.modules.logistics.drivers.domain.value_objects.enums import (
    DriverComplianceStatus,
    DriverEligibilityStatus,
    DriverLifecycleStatus,
)
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverModel,
    DriverVersionModel,
)


class DriverService:
    """Core application service managing drivers."""

    def __init__(self, db: Session):
        self.db = db

    def create_driver(
        self,
        organization_id: UUID,
        first_name: str,
        paternal_last_name: str,
        middle_name: Optional[str] = None,
        maternal_last_name: Optional[str] = None,
        custom_code: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        nationality_country_code: str = "PE",
        notes: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverModel:
        if custom_code:
            code = DriverCodeService.normalize_code(custom_code)
            existing = self.db.scalar(
                select(DriverModel.id).where(
                    DriverModel.organization_id == organization_id,
                    DriverModel.normalized_driver_code == code,
                )
            )
            if existing:
                raise DriverCodeConflict(code)
        else:
            code = DriverCodeService.generate_code(self.db, organization_id)

        norm_code = DriverCodeService.normalize_code(code)

        parts = [first_name.strip()]
        if middle_name:
            parts.append(middle_name.strip())
        parts.append(paternal_last_name.strip())
        if maternal_last_name:
            parts.append(maternal_last_name.strip())

        display_name = " ".join(parts).upper()

        driver = DriverModel(
            organization_id=organization_id,
            driver_code=code,
            normalized_driver_code=norm_code,
            first_name=first_name.strip(),
            middle_name=middle_name.strip() if middle_name else None,
            paternal_last_name=paternal_last_name.strip(),
            maternal_last_name=maternal_last_name.strip() if maternal_last_name else None,
            display_name=display_name,
            date_of_birth=date_of_birth,
            nationality_country_code=nationality_country_code.upper(),
            lifecycle_status=DriverLifecycleStatus.DRAFT.value,
            compliance_status=DriverComplianceStatus.NOT_EVALUATED.value,
            eligibility_status=DriverEligibilityStatus.NOT_EVALUATED.value,
            notes=notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(driver)
        self.db.commit()
        self.db.refresh(driver)

        # Audit
        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.created",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="Driver",
                resource_id=str(driver.id),
                metadata={"driver_code": driver.driver_code, "status": driver.lifecycle_status},
            ),
        )

        return driver

    def get_driver(self, driver_id: UUID, organization_id: Optional[UUID] = None) -> DriverModel:
        stmt = select(DriverModel).where(DriverModel.id == driver_id)
        if organization_id:
            stmt = stmt.where(DriverModel.organization_id == organization_id)
        driver = self.db.scalar(stmt)
        if not driver:
            raise DriverNotFound(str(driver_id))
        return driver

    def list_drivers(
        self,
        organization_id: UUID,
        search: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        compliance_status: Optional[str] = None,
        eligibility_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DriverModel], int]:
        stmt = select(DriverModel).where(DriverModel.organization_id == organization_id)

        if search:
            s_clean = f"%{search.strip().upper()}%"
            stmt = stmt.where(
                (DriverModel.normalized_driver_code.like(s_clean))
                | (DriverModel.display_name.like(s_clean))
            )

        if lifecycle_status:
            stmt = stmt.where(DriverModel.lifecycle_status == lifecycle_status)
        if compliance_status:
            stmt = stmt.where(DriverModel.compliance_status == compliance_status)
        if eligibility_status:
            stmt = stmt.where(DriverModel.eligibility_status == eligibility_status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(DriverModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        drivers = self.db.scalars(stmt).all()

        return list(drivers), total

    def update_driver(
        self,
        driver_id: UUID,
        organization_id: UUID,
        first_name: Optional[str] = None,
        paternal_last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        maternal_last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        notes: Optional[str] = None,
        expected_row_version: Optional[int] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverModel:
        driver = self.get_driver(driver_id, organization_id)

        if expected_row_version is not None and driver.row_version != expected_row_version:
            raise DriverVersionConflict()

        if driver.lifecycle_status in {DriverLifecycleStatus.BLOCKED.value, DriverLifecycleStatus.RETIRED.value, DriverLifecycleStatus.ARCHIVED.value}:
            raise DriverStatusInvalid(driver.lifecycle_status, "update")

        if first_name is not None:
            driver.first_name = first_name.strip()
        if paternal_last_name is not None:
            driver.paternal_last_name = paternal_last_name.strip()
        if middle_name is not None:
            driver.middle_name = middle_name.strip() if middle_name else None
        if maternal_last_name is not None:
            driver.maternal_last_name = maternal_last_name.strip() if maternal_last_name else None
        if date_of_birth is not None:
            driver.date_of_birth = date_of_birth
        if notes is not None:
            driver.notes = notes

        parts = [driver.first_name]
        if driver.middle_name:
            parts.append(driver.middle_name)
        parts.append(driver.paternal_last_name)
        if driver.maternal_last_name:
            parts.append(driver.maternal_last_name)
        driver.display_name = " ".join(parts).upper()

        driver.row_version += 1
        driver.updated_by = actor_id

        self.db.commit()
        self.db.refresh(driver)

        # Audit
        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.updated",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="Driver",
                resource_id=str(driver.id),
                metadata={"driver_code": driver.driver_code, "version": driver.row_version},
            ),
        )

        return driver

    def activate_driver(self, driver_id: UUID, organization_id: UUID, actor_id: Optional[UUID] = None) -> DriverModel:
        driver = self.get_driver(driver_id, organization_id)

        if driver.lifecycle_status == DriverLifecycleStatus.BLOCKED.value:
            raise DriverBlockedError(driver.block_reason or "Conductor bloqueado")
        if driver.lifecycle_status in {DriverLifecycleStatus.RETIRED.value, DriverLifecycleStatus.ARCHIVED.value}:
            raise DriverCannotBeActivated("El conductor está retirado o archivado.")

        # Re-evaluate compliance and eligibility
        comp = DriverDocumentComplianceResolver.resolve_compliance(self.db, driver.id)
        driver.compliance_status = comp.value

        elig = DriverOperationalEligibilityResolver.resolve_eligibility(self.db, driver.id)
        driver.eligibility_status = elig.value

        driver.lifecycle_status = DriverLifecycleStatus.ACTIVE.value
        driver.row_version += 1
        driver.updated_by = actor_id

        # Generate new version snapshot
        self.create_version_snapshot(driver.id, actor_id)

        self.db.commit()
        self.db.refresh(driver)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.activated",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="Driver",
                resource_id=str(driver.id),
                metadata={"driver_code": driver.driver_code, "compliance": driver.compliance_status},
            ),
        )

        return driver

    def block_driver(self, driver_id: UUID, organization_id: UUID, reason: str, actor_id: Optional[UUID] = None) -> DriverModel:
        driver = self.get_driver(driver_id, organization_id)

        if driver.lifecycle_status == DriverLifecycleStatus.BLOCKED.value:
            return driver

        driver.lifecycle_status = DriverLifecycleStatus.BLOCKED.value
        driver.eligibility_status = DriverEligibilityStatus.BLOCKED.value
        driver.blocked_at = utc_now()
        driver.blocked_by = actor_id
        driver.block_reason = reason
        driver.row_version += 1
        driver.updated_by = actor_id

        self.db.commit()
        self.db.refresh(driver)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.blocked",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="Driver",
                resource_id=str(driver.id),
                metadata={"driver_code": driver.driver_code, "reason": reason},
            ),
        )

        return driver

    def unblock_driver(self, driver_id: UUID, organization_id: UUID, actor_id: Optional[UUID] = None) -> DriverModel:
        driver = self.get_driver(driver_id, organization_id)

        if driver.lifecycle_status != DriverLifecycleStatus.BLOCKED.value:
            return driver

        driver.lifecycle_status = DriverLifecycleStatus.INACTIVE.value
        driver.blocked_at = None
        driver.blocked_by = None
        driver.block_reason = None
        driver.row_version += 1
        driver.updated_by = actor_id

        # Re-evaluate
        comp = DriverDocumentComplianceResolver.resolve_compliance(self.db, driver.id)
        driver.compliance_status = comp.value
        elig = DriverOperationalEligibilityResolver.resolve_eligibility(self.db, driver.id)
        driver.eligibility_status = elig.value

        self.db.commit()
        self.db.refresh(driver)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.unblocked",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="Driver",
                resource_id=str(driver.id),
                metadata={"driver_code": driver.driver_code},
            ),
        )

        return driver

    def create_version_snapshot(self, driver_id: UUID, actor_id: Optional[UUID] = None) -> DriverVersionModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        snapshots = DriverSnapshotProvider.create_snapshots(self.db, driver_id)

        # Get next version number
        last_ver = self.db.scalar(
            select(func.max(DriverVersionModel.version)).where(DriverVersionModel.driver_id == driver_id)
        ) or 0
        next_ver = last_ver + 1

        version_obj = DriverVersionModel(
            driver_id=driver_id,
            version=next_ver,
            status="ACTIVE",
            identity_snapshot=snapshots["identity_snapshot"],
            license_snapshot=snapshots["license_snapshot"],
            categories_snapshot=snapshots["categories_snapshot"],
            carrier_snapshot=snapshots["carrier_snapshot"],
            contact_snapshot=snapshots["contact_snapshot"],
            photo_snapshot=snapshots["photo_snapshot"],
            restrictions_snapshot=snapshots["restrictions_snapshot"],
            compliance_snapshot=snapshots["compliance_snapshot"],
            eligibility_snapshot=snapshots["eligibility_snapshot"],
            content_hash=snapshots["content_hash"],
            created_by=actor_id,
        )
        self.db.add(version_obj)
        self.db.flush()

        driver.active_version_id = version_obj.id

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.version_created",
                actor_user_id=actor_id,
                organization_id=driver.organization_id,
                resource_type="DriverVersion",
                resource_id=str(version_obj.id),
                metadata={"driver_code": driver.driver_code, "version": next_ver},
            ),
        )

        return version_obj
