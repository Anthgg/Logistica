"""Compliance and Risk Resolver for Business Partners (Phase 025)."""

from datetime import datetime, timezone
from typing import Dict, List, Any
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerDocumentModel,
    BusinessPartnerDocumentRequirementModel,
    BusinessPartnerRoleModel,
    BusinessPartnerEvaluationModel,
)


class BusinessPartnerComplianceResolver:
    """Evaluates partner documents and evaluations to determine compliance and risk status."""

    @classmethod
    def resolve_compliance(cls, db: Session, partner_id: UUID) -> Dict[str, Any]:
        partner = db.get(BusinessPartnerModel, partner_id)
        if not partner:
            return {"compliance_status": "NOT_EVALUATED", "risk_status": "NOT_EVALUATED"}

        # Get active roles
        roles_stmt = select(BusinessPartnerRoleModel.role_type).where(
            and_(
                BusinessPartnerRoleModel.business_partner_id == partner_id,
                BusinessPartnerRoleModel.status == "ACTIVE",
            )
        )
        active_roles = db.scalars(roles_stmt).all()

        # Get required documents for active roles
        reqs_stmt = select(BusinessPartnerDocumentRequirementModel).where(
            and_(
                BusinessPartnerDocumentRequirementModel.organization_id == partner.organization_id,
                BusinessPartnerDocumentRequirementModel.role_type.in_(active_roles) if active_roles else False,
                BusinessPartnerDocumentRequirementModel.status == "ACTIVE",
            )
        )
        reqs = db.scalars(reqs_stmt).all()

        # Get existing documents
        docs_stmt = select(BusinessPartnerDocumentModel).where(
            and_(
                BusinessPartnerDocumentModel.business_partner_id == partner_id,
                BusinessPartnerDocumentModel.status == "ACTIVE",
            )
        )
        docs = db.scalars(docs_stmt).all()

        now = utc_now()
        missing_count = 0
        expired_count = 0
        blocking_count = 0

        existing_doc_types = {d.document_type: d for d in docs}

        for req in reqs:
            doc = existing_doc_types.get(req.document_type)
            if not doc:
                if req.required:
                    missing_count += 1
                    if req.blocking:
                        blocking_count += 1
            else:
                if req.requires_expiration and doc.expires_at and doc.expires_at < now:
                    expired_count += 1
                    if req.blocking:
                        blocking_count += 1

        if blocking_count > 0 or expired_count > 0:
            compliance_status = "DOCUMENTS_EXPIRED" if expired_count > 0 else "NON_COMPLIANT"
        elif missing_count > 0:
            compliance_status = "PARTIALLY_COMPLIANT"
        else:
            compliance_status = "COMPLIANT"

        # Resolve risk status from latest evaluations
        eval_stmt = (
            select(BusinessPartnerEvaluationModel.risk_level)
            .where(
                and_(
                    BusinessPartnerEvaluationModel.business_partner_id == partner_id,
                    BusinessPartnerEvaluationModel.status == "APPROVED",
                )
            )
            .order_by(BusinessPartnerEvaluationModel.created_at.desc())
        )
        latest_risk = db.scalars(eval_stmt).first() or "LOW"

        return {
            "compliance_status": compliance_status,
            "risk_status": latest_risk,
            "missing_documents_count": missing_count,
            "expired_documents_count": expired_count,
            "blocking_issues_count": blocking_count,
        }
