"""Business Partner Snapshot Provider (Phase 025)."""

import hashlib
import json
from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerIdentifierModel,
    BusinessPartnerAddressModel,
    BusinessPartnerContactModel,
    BusinessPartnerRoleModel,
)


class BusinessPartnerSnapshotProvider:
    """Generates deterministic immutable JSONB snapshots and SHA-256 hashes of partners."""

    @staticmethod
    def calculate_content_hash(payload: Dict[str, Any]) -> str:
        """Return a stable SHA-256 hash for an arbitrary snapshot payload."""
        canonical_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()

    @classmethod
    def build_snapshot_dict(
        cls,
        partner: BusinessPartnerModel,
        db: Session,
    ) -> Dict[str, Any]:
        """Compatibility entry point used by the RUC integration workflow."""
        return cls.create_snapshot(db, partner.id)["snapshot_data"]

    @classmethod
    def create_snapshot(cls, db: Session, partner_id: UUID) -> Dict[str, Any]:
        partner = db.get(BusinessPartnerModel, partner_id)
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")

        # Fetch identifiers
        idents = db.scalars(
            select(BusinessPartnerIdentifierModel).where(
                BusinessPartnerIdentifierModel.business_partner_id == partner_id
            )
        ).all()

        # Fetch addresses
        addresses = db.scalars(
            select(BusinessPartnerAddressModel).where(
                BusinessPartnerAddressModel.business_partner_id == partner_id
            )
        ).all()

        # Fetch contacts
        contacts = db.scalars(
            select(BusinessPartnerContactModel).where(
                BusinessPartnerContactModel.business_partner_id == partner_id
            )
        ).all()

        # Fetch roles
        roles = db.scalars(
            select(BusinessPartnerRoleModel).where(
                BusinessPartnerRoleModel.business_partner_id == partner_id
            )
        ).all()

        snapshot_data = {
            "partner_id": str(partner.id),
            "organization_id": str(partner.organization_id),
            "partner_code": partner.partner_code,
            "legal_name": partner.legal_name,
            "trade_name": partner.trade_name,
            "person_type": partner.person_type,
            "country_code": partner.country_code,
            "status": partner.status,
            "risk_status": partner.risk_status,
            "compliance_status": partner.compliance_status,
            "roles": [r.role_type for r in roles if r.status == "ACTIVE"],
            "primary_identifier": next(
                (
                    {"type": i.identifier_type, "value": i.value, "status": i.verification_status}
                    for i in idents if i.is_primary and i.status == "ACTIVE"
                ),
                None,
            ),
            "primary_address": next(
                (
                    {
                        "type": a.address_type,
                        "line_1": a.address_line_1,
                        "district": a.district,
                        "province": a.province,
                        "department": a.department,
                    }
                    for a in addresses if a.is_primary and a.status == "ACTIVE"
                ),
                None,
            ),
            "primary_contact": next(
                (
                    {
                        "name": c.full_name,
                        "email": c.email,
                        "phone": c.phone,
                        "type": c.contact_type,
                    }
                    for c in contacts if c.is_primary and c.status == "ACTIVE"
                ),
                None,
            ),
            "captured_at": utc_now().isoformat(),
        }

        content_hash = cls.calculate_content_hash(snapshot_data)

        return {
            "snapshot_data": snapshot_data,
            "content_hash": content_hash,
        }
