"""InstitutionalSnapshotProvider — Provides canonical snapshot of company data for document issuance (Phase 021)."""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.company_profile.company_profile_service import CompanyProfileService


class InstitutionalSnapshotProvider:
    """Captures active institutional state to store inside DocumentSnapshot (Phase 021)."""

    def __init__(self, db: Session):
        self.db = db
        self.profile_srv = CompanyProfileService(db)

    def capture_snapshot(self, organization_id: UUID) -> dict[str, Any]:
        profile = self.profile_srv.get_profile_or_create_default(organization_id)
        payload, content_hash = self.profile_srv.build_canonical_payload(organization_id)

        snapshot = {
            "organization_id": str(organization_id),
            "profile_id": str(profile.id),
            "active_version_id": str(profile.active_version_id) if profile.active_version_id else None,
            "legal_name": profile.legal_name,
            "trade_name": profile.trade_name,
            "ruc": profile.ruc,
            "country_code": profile.country_code,
            "locale": profile.locale,
            "timezone": profile.timezone,
            "currency": profile.default_currency,
            "verification_status": profile.verification_status,
            "institutional_payload": payload,
            "content_hash": content_hash,
            "captured_at": utc_now().isoformat(),
        }

        return snapshot
