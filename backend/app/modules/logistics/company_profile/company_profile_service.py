"""Company Profile application service (Phase 021)."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.company_profile.models import (
    OrganizationAddressModel,
    OrganizationAssetModel,
    OrganizationContactModel,
    OrganizationDocumentSettingsModel,
    OrganizationProfileModel,
    OrganizationProfileVersionModel,
)
from app.modules.logistics.company_profile.schemas import (
    OrganizationProfileCreate,
    OrganizationProfileUpdate,
)
from app.modules.logistics.company_profile.validators import generate_valid_ruc, validate_peruvian_ruc


class CompanyProfileService:
    """Service managing OrganizationProfile, SemVer versioning, and canonical payloads."""

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, organization_id: UUID) -> OrganizationProfileModel | None:
        return self.db.scalars(
            select(OrganizationProfileModel).where(OrganizationProfileModel.organization_id == organization_id)
        ).first()

    def get_profile_or_create_default(self, organization_id: UUID, actor_id: UUID | None = None) -> OrganizationProfileModel:
        profile = self.get_profile(organization_id)
        if not profile:
            # Query organization name from logistics_organizations table if available
            from app.models.organization import Organization
            org = self.db.get(Organization, organization_id)
            legal_name = org.name if org else "Organización Demo S.A.C."
            ruc = generate_valid_ruc(str(organization_id))  # Unique valid Modulo 11 RUC per organization

            profile = OrganizationProfileModel(
                organization_id=organization_id,
                legal_name=legal_name,
                trade_name=legal_name,
                ruc=ruc,
                country_code="PE",
                locale="es-PE",
                timezone="America/Lima",
                default_currency="PEN",
                document_language="es",
                profile_status="DRAFT",
                verification_status="FORMAT_VALID",
                created_by=actor_id,
            )
            self.db.add(profile)
            self.db.flush()

            # Create default document settings
            settings = OrganizationDocumentSettingsModel(
                organization_id=organization_id,
                show_ruc=True,
                show_trade_name=True,
                show_legal_name=True,
                show_address=True,
                show_contact=True,
                status="ACTIVE",
            )
            self.db.add(settings)
            self.db.flush()

        return profile

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

    def update_profile(
        self, organization_id: UUID, req: OrganizationProfileUpdate, actor_id: UUID | None = None
    ) -> OrganizationProfileModel:
        profile = self.get_profile_or_create_default(organization_id, actor_id)

        prev_version = profile.profile_status
        changes = {}

        if req.ruc is not None and req.ruc != profile.ruc:
            is_valid, msg = validate_peruvian_ruc(req.ruc)
            if not is_valid:
                raise HTTPException(status_code=400, detail=msg)

            # Check uniqueness across orgs
            existing = self.db.scalars(
                select(OrganizationProfileModel).where(
                    and_(OrganizationProfileModel.ruc == req.ruc, OrganizationProfileModel.id != profile.id)
                )
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="El RUC ingresado ya pertenece a otra organización.")

            changes["ruc"] = (profile.ruc, req.ruc)
            profile.ruc = req.ruc

        for field in [
            "legal_name", "trade_name", "legal_entity_type", "economic_activity",
            "website", "primary_email", "primary_phone", "country_code",
            "locale", "timezone", "default_currency", "document_language"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                curr_val = getattr(profile, field)
                if curr_val != val:
                    changes[field] = (str(curr_val), str(val))
                    setattr(profile, field, val)

        profile.updated_by = actor_id
        profile.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_profile.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_profiles",
            resource_id=profile.id,
            details={"changes": json.loads(json.dumps(changes, default=str))},
        )

        return profile

    def build_canonical_payload(self, organization_id: UUID) -> tuple[dict[str, Any], str]:
        """Compiles profile, addresses, contacts, settings and logo into a deterministic canonical dictionary."""
        profile = self.get_profile_or_create_default(organization_id)

        addresses = self.db.scalars(
            select(OrganizationAddressModel).where(
                and_(OrganizationAddressModel.organization_id == organization_id, OrganizationAddressModel.status == "ACTIVE")
            )
        ).all()

        contacts = self.db.scalars(
            select(OrganizationContactModel).where(
                and_(OrganizationContactModel.organization_id == organization_id, OrganizationContactModel.status == "ACTIVE")
            )
        ).all()

        settings = self.db.scalars(
            select(OrganizationDocumentSettingsModel).where(OrganizationDocumentSettingsModel.organization_id == organization_id)
        ).first()

        doc_logo = None
        if settings and settings.document_logo_asset_id:
            asset = self.db.get(OrganizationAssetModel, settings.document_logo_asset_id)
            if asset and asset.status == "ACTIVE":
                doc_logo = {
                    "asset_id": str(asset.id),
                    "filename": asset.filename,
                    "file_hash": asset.file_hash,
                    "mime_type": asset.mime_type,
                    "size_bytes": asset.size_bytes,
                }

        payload = {
            "organization_id": str(profile.organization_id),
            "legal_name": profile.legal_name,
            "trade_name": profile.trade_name,
            "ruc": profile.ruc,
            "legal_entity_type": profile.legal_entity_type,
            "country_code": profile.country_code,
            "locale": profile.locale,
            "timezone": profile.timezone,
            "default_currency": profile.default_currency,
            "document_language": profile.document_language,
            "addresses": [
                {
                    "id": str(a.id),
                    "address_type": a.address_type,
                    "label": a.label,
                    "address_line": a.address_line,
                    "district": a.district,
                    "province": a.province,
                    "department": a.department,
                    "is_primary": a.is_primary,
                    "is_document_address": a.is_document_address,
                }
                for a in sorted(addresses, key=lambda x: str(x.id))
            ],
            "contacts": [
                {
                    "id": str(c.id),
                    "contact_type": c.contact_type,
                    "label": c.label,
                    "full_name": c.full_name,
                    "email": c.email,
                    "phone": c.phone,
                    "is_primary": c.is_primary,
                    "show_in_documents": c.show_in_documents,
                }
                for c in sorted(contacts, key=lambda x: str(x.id))
            ],
            "document_settings": {
                "show_ruc": settings.show_ruc if settings else True,
                "show_trade_name": settings.show_trade_name if settings else True,
                "show_legal_name": settings.show_legal_name if settings else True,
                "show_address": settings.show_address if settings else True,
                "show_contact": settings.show_contact if settings else True,
                "confidentiality_text": settings.confidentiality_text if settings else None,
                "footer_text": settings.footer_text if settings else None,
                "logo": doc_logo,
            },
        }

        canonical_json = json.dumps(payload, sort_keys=True, default=str)
        content_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
        return payload, content_hash

    def create_version(self, organization_id: UUID, actor_id: UUID | None = None) -> OrganizationProfileVersionModel:
        profile = self.get_profile_or_create_default(organization_id, actor_id)
        payload, content_hash = self.build_canonical_payload(organization_id)

        # Calculate next version
        existing_versions = self.db.scalars(
            select(OrganizationProfileVersionModel).where(
                OrganizationProfileVersionModel.organization_profile_id == profile.id
            )
        ).all()

        if not existing_versions:
            next_ver = "1.0.0"
        else:
            # Parse SemVer integer patch
            versions_parsed = []
            for v in existing_versions:
                parts = v.version.split(".")
                if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
                    versions_parsed.append((int(parts[0]), int(parts[1]), int(parts[2])))
            if versions_parsed:
                versions_parsed.sort()
                major, minor, patch = versions_parsed[-1]
                next_ver = f"{major}.{minor}.{patch + 1}"
            else:
                next_ver = f"1.0.{len(existing_versions)}"

        ver_obj = OrganizationProfileVersionModel(
            organization_profile_id=profile.id,
            version=next_ver,
            status="DRAFT",
            legal_name=profile.legal_name,
            trade_name=profile.trade_name,
            ruc=profile.ruc,
            institutional_payload=payload,
            content_hash=content_hash,
            created_by=actor_id,
        )
        self.db.add(ver_obj)
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_profile.version_created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_profile_versions",
            resource_id=ver_obj.id,
            details={"version": next_ver, "content_hash": content_hash},
        )

        return ver_obj

    def activate_version(
        self, organization_id: UUID, version_id: UUID, reason: str, actor_id: UUID | None = None
    ) -> OrganizationProfileVersionModel:
        profile = self.get_profile_or_create_default(organization_id, actor_id)

        version_obj = self.db.get(OrganizationProfileVersionModel, version_id)
        if not version_obj or version_obj.organization_profile_id != profile.id:
            raise HTTPException(status_code=404, detail="OrganizationProfileVersion not found.")

        now = utc_now()

        # Deprecate current active version if exists
        if profile.active_version_id:
            curr_active = self.db.get(OrganizationProfileVersionModel, profile.active_version_id)
            if curr_active:
                curr_active.status = "DEPRECATED"
                curr_active.effective_to = now

        version_obj.status = "ACTIVE"
        version_obj.effective_from = now
        version_obj.effective_to = None
        version_obj.approved_by = actor_id
        version_obj.approved_at = now

        profile.active_version_id = version_obj.id
        profile.profile_status = "ACTIVE"
        profile.updated_by = actor_id
        profile.updated_at = now

        self.db.flush()

        self._write_audit(
            event_code="logistics.company_profile.version_activated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_profile_versions",
            resource_id=version_obj.id,
            details={"version": version_obj.version, "reason": reason, "content_hash": version_obj.content_hash},
        )

        return version_obj
