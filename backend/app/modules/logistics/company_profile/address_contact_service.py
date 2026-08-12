"""Service for managing institutional addresses and contacts (Phase 021)."""

import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.company_profile.models import (
    OrganizationAddressModel,
    OrganizationContactModel,
)
from app.modules.logistics.company_profile.schemas import (
    OrganizationAddressCreate,
    OrganizationAddressUpdate,
    OrganizationContactCreate,
    OrganizationContactUpdate,
)


class AddressContactService:
    def __init__(self, db: Session):
        self.db = db

    def _write_audit(self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_type: str, resource_id: Any, details: dict):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    # --- Addresses ---

    def list_addresses(self, organization_id: UUID) -> list[OrganizationAddressModel]:
        return self.db.scalars(
            select(OrganizationAddressModel)
            .where(OrganizationAddressModel.organization_id == organization_id)
            .order_by(OrganizationAddressModel.is_primary.desc(), OrganizationAddressModel.created_at.desc())
        ).all()

    def create_address(
        self, organization_id: UUID, req: OrganizationAddressCreate, actor_id: UUID | None = None
    ) -> OrganizationAddressModel:
        if req.is_primary:
            # Demote existing primary address of same type if present
            self.db.execute(
                update(OrganizationAddressModel)
                .where(
                    and_(
                        OrganizationAddressModel.organization_id == organization_id,
                        OrganizationAddressModel.address_type == req.address_type,
                        OrganizationAddressModel.is_primary == True,
                    )
                )
                .values(is_primary=False)
            )

        addr = OrganizationAddressModel(
            organization_id=organization_id,
            branch_id=req.branch_id,
            address_type=req.address_type.upper(),
            label=req.label,
            address_line=req.address_line,
            district=req.district,
            province=req.province,
            department=req.department,
            postal_code=req.postal_code,
            country_code=req.country_code.upper(),
            latitude=req.latitude,
            longitude=req.longitude,
            is_primary=req.is_primary,
            is_document_address=req.is_document_address,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(addr)
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_address.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_addresses",
            resource_id=addr.id,
            details={"label": addr.label, "address_type": addr.address_type},
        )

        return addr

    def update_address(
        self, organization_id: UUID, address_id: UUID, req: OrganizationAddressUpdate, actor_id: UUID | None = None
    ) -> OrganizationAddressModel:
        addr = self.db.get(OrganizationAddressModel, address_id)
        if not addr or addr.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationAddress not found.")

        if req.is_primary is True and not addr.is_primary:
            self.db.execute(
                update(OrganizationAddressModel)
                .where(
                    and_(
                        OrganizationAddressModel.organization_id == organization_id,
                        OrganizationAddressModel.address_type == (req.address_type or addr.address_type),
                        OrganizationAddressModel.is_primary == True,
                    )
                )
                .values(is_primary=False)
            )

        for field in [
            "branch_id", "address_type", "label", "address_line", "district",
            "province", "department", "postal_code", "country_code", "latitude",
            "longitude", "is_primary", "is_document_address"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                if field in ("address_type", "country_code") and isinstance(val, str):
                    val = val.upper()
                setattr(addr, field, val)

        addr.updated_by = actor_id
        addr.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_address.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_addresses",
            resource_id=addr.id,
            details={"label": addr.label},
        )

        return addr

    def set_primary_address(self, organization_id: UUID, address_id: UUID, actor_id: UUID | None = None) -> OrganizationAddressModel:
        addr = self.db.get(OrganizationAddressModel, address_id)
        if not addr or addr.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationAddress not found.")

        self.db.execute(
            update(OrganizationAddressModel)
            .where(
                and_(
                    OrganizationAddressModel.organization_id == organization_id,
                    OrganizationAddressModel.address_type == addr.address_type,
                    OrganizationAddressModel.is_primary == True,
                )
            )
            .values(is_primary=False)
        )

        addr.is_primary = True
        addr.updated_by = actor_id
        addr.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_address.primary_changed",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_addresses",
            resource_id=addr.id,
            details={"address_type": addr.address_type},
        )

        return addr

    def set_address_status(self, organization_id: UUID, address_id: UUID, status: str, actor_id: UUID | None = None) -> OrganizationAddressModel:
        addr = self.db.get(OrganizationAddressModel, address_id)
        if not addr or addr.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationAddress not found.")

        addr.status = status.upper()
        addr.updated_by = actor_id
        addr.updated_at = utc_now()
        self.db.flush()
        return addr

    # --- Contacts ---

    def list_contacts(self, organization_id: UUID) -> list[OrganizationContactModel]:
        return self.db.scalars(
            select(OrganizationContactModel)
            .where(OrganizationContactModel.organization_id == organization_id)
            .order_by(OrganizationContactModel.is_primary.desc(), OrganizationContactModel.created_at.desc())
        ).all()

    def create_contact(
        self, organization_id: UUID, req: OrganizationContactCreate, actor_id: UUID | None = None
    ) -> OrganizationContactModel:
        if req.is_primary:
            self.db.execute(
                update(OrganizationContactModel)
                .where(
                    and_(
                        OrganizationContactModel.organization_id == organization_id,
                        OrganizationContactModel.contact_type == req.contact_type,
                        OrganizationContactModel.is_primary == True,
                    )
                )
                .values(is_primary=False)
            )

        contact = OrganizationContactModel(
            organization_id=organization_id,
            branch_id=req.branch_id,
            contact_type=req.contact_type.upper(),
            label=req.label,
            full_name=req.full_name,
            position=req.position,
            email=str(req.email) if req.email else None,
            phone=req.phone,
            extension=req.extension,
            website=req.website,
            is_primary=req.is_primary,
            show_in_documents=req.show_in_documents,
            document_families=req.document_families,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(contact)
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_contact.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_contacts",
            resource_id=contact.id,
            details={"label": contact.label, "contact_type": contact.contact_type},
        )

        return contact

    def update_contact(
        self, organization_id: UUID, contact_id: UUID, req: OrganizationContactUpdate, actor_id: UUID | None = None
    ) -> OrganizationContactModel:
        contact = self.db.get(OrganizationContactModel, contact_id)
        if not contact or contact.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationContact not found.")

        if req.is_primary is True and not contact.is_primary:
            self.db.execute(
                update(OrganizationContactModel)
                .where(
                    and_(
                        OrganizationContactModel.organization_id == organization_id,
                        OrganizationContactModel.contact_type == (req.contact_type or contact.contact_type),
                        OrganizationContactModel.is_primary == True,
                    )
                )
                .values(is_primary=False)
            )

        for field in [
            "branch_id", "contact_type", "label", "full_name", "position",
            "phone", "extension", "website", "is_primary", "show_in_documents",
            "document_families"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                if field == "contact_type" and isinstance(val, str):
                    val = val.upper()
                setattr(contact, field, val)

        if req.email is not None:
            contact.email = str(req.email)

        contact.updated_by = actor_id
        contact.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_contact.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_contacts",
            resource_id=contact.id,
            details={"label": contact.label},
        )

        return contact

    def set_primary_contact(self, organization_id: UUID, contact_id: UUID, actor_id: UUID | None = None) -> OrganizationContactModel:
        contact = self.db.get(OrganizationContactModel, contact_id)
        if not contact or contact.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationContact not found.")

        self.db.execute(
            update(OrganizationContactModel)
            .where(
                and_(
                    OrganizationContactModel.organization_id == organization_id,
                    OrganizationContactModel.contact_type == contact.contact_type,
                    OrganizationContactModel.is_primary == True,
                )
            )
            .values(is_primary=False)
        )

        contact.is_primary = True
        contact.updated_by = actor_id
        contact.updated_at = utc_now()
        self.db.flush()
        return contact

    def set_contact_status(self, organization_id: UUID, contact_id: UUID, status: str, actor_id: UUID | None = None) -> OrganizationContactModel:
        contact = self.db.get(OrganizationContactModel, contact_id)
        if not contact or contact.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="OrganizationContact not found.")

        contact.status = status.upper()
        contact.updated_by = actor_id
        contact.updated_at = utc_now()
        self.db.flush()
        return contact
