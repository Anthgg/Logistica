"""Business Partner Code generator and normalizer (Phase 025)."""

import re
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.partners.models import BusinessPartnerModel


class BusinessPartnerCodeService:
    @staticmethod
    def normalize_code(code: str) -> str:
        if not code:
            return ""
        return re.sub(r"[^A-Z0-9-]", "", code.upper().strip())

    @classmethod
    def generate_next_code(cls, db: Session, organization_id: UUID, prefix: str = "BP") -> str:
        prefix_norm = prefix.upper().strip()
        stmt = (
            select(func.count(BusinessPartnerModel.id))
            .where(BusinessPartnerModel.organization_id == organization_id)
        )
        count = db.scalar(stmt) or 0
        sequence = count + 1
        return f"{prefix_norm}-{sequence:06d}"
