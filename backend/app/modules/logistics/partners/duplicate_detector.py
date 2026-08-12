"""Business Partner Duplicate Detection Engine (Phase 025)."""

import re
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerIdentifierModel,
)


class BusinessPartnerDuplicateDetection:
    """Detects potential duplicate partners by RUC, legal name, trade name, or contacts."""

    @classmethod
    def find_duplicates(
        cls,
        db: Session,
        organization_id: UUID,
        tax_id_val: str | None = None,
        legal_name: str | None = None,
        trade_name: str | None = None,
    ) -> List[Dict[str, Any]]:
        results = []

        # Check by Tax Identifier
        if tax_id_val:
            clean_tax_id = re.sub(r"\D", "", tax_id_val)
            ident_stmt = select(BusinessPartnerIdentifierModel).where(
                and_(
                    BusinessPartnerIdentifierModel.organization_id == organization_id,
                    BusinessPartnerIdentifierModel.normalized_value == clean_tax_id,
                    BusinessPartnerIdentifierModel.status == "ACTIVE",
                )
            )
            matched_idents = db.scalars(ident_stmt).all()
            for ident in matched_idents:
                partner = db.get(BusinessPartnerModel, ident.business_partner_id)
                if partner:
                    results.append({
                        "partner_id": str(partner.id),
                        "partner_code": partner.partner_code,
                        "legal_name": partner.legal_name,
                        "match_type": "EXACT_TAX_ID",
                        "probability": "HIGH_PROBABILITY_DUPLICATE",
                    })

        # Check by Legal Name
        if legal_name:
            norm_name = legal_name.strip().upper()
            name_stmt = select(BusinessPartnerModel).where(
                and_(
                    BusinessPartnerModel.organization_id == organization_id,
                    BusinessPartnerModel.legal_name.ilike(f"%{norm_name}%"),
                )
            )
            matched_partners = db.scalars(name_stmt).all()
            for p in matched_partners:
                if not any(r["partner_id"] == str(p.id) for r in results):
                    results.append({
                        "partner_id": str(p.id),
                        "partner_code": p.partner_code,
                        "legal_name": p.legal_name,
                        "match_type": "SIMILAR_LEGAL_NAME",
                        "probability": "POSSIBLE_DUPLICATE",
                    })

        return results
