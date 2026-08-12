"""Services for Driver Documents, Requirements and Operational Restrictions."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.drivers.domain.errors.exceptions import (
    DriverDocumentNotFound,
    DriverNotFound,
    DriverRestrictionNotFound,
)
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverDocumentModel,
    DriverDocumentRequirementModel,
    DriverModel,
    DriverOperationalRestrictionModel,
)


class DriverDocumentService:
    def __init__(self, db: Session):
        self.db = db

    def add_document(
        self,
        driver_id: UUID,
        document_type: str,
        document_number: Optional[str] = None,
        issuer: Optional[str] = None,
        issued_at: Optional[date] = None,
        valid_from: Optional[date] = None,
        expires_at: Optional[date] = None,
        file_reference_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverDocumentModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        doc = DriverDocumentModel(
            driver_id=driver_id,
            document_type=document_type.upper(),
            document_number=document_number.strip() if document_number else None,
            issuer=issuer.strip() if issuer else None,
            issued_at=issued_at,
            valid_from=valid_from or date.today(),
            expires_at=expires_at,
            verification_status="METADATA_REVIEWED",
            status="ACTIVE",
            file_reference_id=file_reference_id,
            source_type="MANUAL_UPLOAD",
            notes=notes,
            created_by=actor_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.document_created",
                actor_user_id=actor_id,
                organization_id=driver.organization_id,
                resource_type="DriverDocument",
                resource_id=str(doc.id),
                metadata={"driver_id": str(driver_id), "document_type": document_type},
            ),
        )

        return doc


class DriverOperationalRestrictionService:
    def __init__(self, db: Session):
        self.db = db

    def add_restriction(
        self,
        driver_id: UUID,
        restriction_type: str,
        description: str,
        reason: str,
        severity: str = "CRITICAL",
        blocking: bool = True,
        valid_until: Optional[date] = None,
        actor_id: Optional[UUID] = None,
    ) -> DriverOperationalRestrictionModel:
        driver = self.db.get(DriverModel, driver_id)
        if not driver:
            raise DriverNotFound(str(driver_id))

        rest = DriverOperationalRestrictionModel(
            driver_id=driver_id,
            restriction_type=restriction_type.upper(),
            source_type="ADMINISTRATIVE",
            severity=severity.upper(),
            blocking=blocking,
            description=description,
            reason=reason,
            valid_from=utc_now(),
            valid_until=datetime.combine(valid_until, datetime.min.time()).replace(tzinfo=utc_now().tzinfo) if valid_until else None,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(rest)
        self.db.commit()
        self.db.refresh(rest)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.driver.restriction_created",
                actor_user_id=actor_id,
                organization_id=driver.organization_id,
                resource_type="DriverOperationalRestriction",
                resource_id=str(rest.id),
                metadata={"driver_id": str(driver_id), "type": restriction_type, "blocking": blocking},
            ),
        )

        return rest

    def revoke_restriction(
        self,
        restriction_id: UUID,
        reason: str,
        actor_id: Optional[UUID] = None,
    ) -> DriverOperationalRestrictionModel:
        rest = self.db.get(DriverOperationalRestrictionModel, restriction_id)
        if not rest:
            raise DriverRestrictionNotFound(str(restriction_id))

        rest.status = "REVOKED"
        rest.revoked_by = actor_id
        rest.revoked_at = utc_now()
        rest.revocation_reason = reason

        self.db.commit()
        self.db.refresh(rest)

        driver = self.db.get(DriverModel, rest.driver_id)
        if driver:
            audit_service.write_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.driver.restriction_revoked",
                    actor_user_id=actor_id,
                    organization_id=driver.organization_id,
                    resource_type="DriverOperationalRestriction",
                    resource_id=str(rest.id),
                    metadata={"driver_id": str(driver.id), "reason": reason},
                ),
            )

        return rest
