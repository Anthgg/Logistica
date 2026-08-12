"""Business Partner Application Service (Phase 025)."""

import json
from decimal import Decimal
from typing import Any, List, Optional, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.partners.code_service import BusinessPartnerCodeService
from app.modules.logistics.partners.compliance_resolver import BusinessPartnerComplianceResolver
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerVersionModel,
    BusinessPartnerAliasModel,
    BusinessPartnerRoleModel,
    SupplierProfileModel,
    CustomerProfileModel,
    CarrierProfileModel,
    BusinessPartnerIdentifierModel,
    BusinessPartnerAddressModel,
    BusinessPartnerContactModel,
    BusinessPartnerOperationalSettingsModel,
    BusinessPartnerEvaluationTemplateModel,
    BusinessPartnerEvaluationModel,
    BusinessPartnerEvaluationCriterionModel,
    BusinessPartnerDocumentRequirementModel,
    BusinessPartnerDocumentModel,
)
from app.modules.logistics.partners.ruc_validator import PeruvianRucValidator
from app.modules.logistics.partners.snapshot_provider import BusinessPartnerSnapshotProvider


class BusinessPartnerService:
    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self,
        event_code: str,
        organization_id: UUID,
        actor_id: UUID | None,
        resource_id: Any,
        details: dict,
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="business_partner",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.record_event(self.db, cmd)

    def create_partner(
        self,
        organization_id: UUID,
        legal_name: str,
        trade_name: str | None = None,
        person_type: str = "LEGAL_ENTITY",
        country_code: str = "PE",
        tax_id_type: str | None = None,
        tax_id_value: str | None = None,
        roles: List[str] | None = None,
        actor_id: UUID | None = None,
    ) -> BusinessPartnerModel:
        if not legal_name or not legal_name.strip():
            raise HTTPException(status_code=400, detail="legal_name is required")

        partner_code = BusinessPartnerCodeService.generate_next_code(self.db, organization_id)
        norm_code = BusinessPartnerCodeService.normalize_code(partner_code)

        partner = BusinessPartnerModel(
            organization_id=organization_id,
            partner_code=partner_code,
            normalized_partner_code=norm_code,
            legal_name=legal_name.strip(),
            trade_name=trade_name.strip() if trade_name else None,
            person_type=person_type,
            country_code=country_code,
            status="DRAFT",
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(partner)
        self.db.flush()

        # Add Tax Identifier if provided
        if tax_id_type and tax_id_value:
            norm_val = tax_id_value.strip()
            verification_status = "NOT_VERIFIED"

            if tax_id_type.upper() == "RUC" and country_code == "PE":
                norm_val = PeruvianRucValidator.normalize(tax_id_value)
                if PeruvianRucValidator.validate(norm_val):
                    verification_status = "FORMAT_VALID"
                else:
                    raise HTTPException(status_code=400, detail="Invalid Peruvian RUC syntax")

            identifier = BusinessPartnerIdentifierModel(
                organization_id=organization_id,
                business_partner_id=partner.id,
                identifier_type=tax_id_type.upper(),
                country_code=country_code,
                value=tax_id_value,
                normalized_value=norm_val,
                is_primary=True,
                verification_status=verification_status,
                created_by=actor_id,
            )
            self.db.add(identifier)

        # Add initial roles if provided
        if roles:
            for r_type in set(roles):
                r_upper = r_type.upper()
                role = BusinessPartnerRoleModel(
                    business_partner_id=partner.id,
                    role_type=r_upper,
                    status="ACTIVE",
                    created_by=actor_id,
                )
                self.db.add(role)
                self.db.flush()

                if r_upper == "SUPPLIER":
                    sp = SupplierProfileModel(business_partner_role_id=role.id)
                    self.db.add(sp)
                elif r_upper == "CUSTOMER":
                    cp = CustomerProfileModel(business_partner_role_id=role.id)
                    self.db.add(cp)
                elif r_upper == "CARRIER":
                    crp = CarrierProfileModel(business_partner_role_id=role.id)
                    self.db.add(crp)

        self.db.flush()

        # Create initial Version & Snapshot
        snap_res = BusinessPartnerSnapshotProvider.create_snapshot(self.db, partner.id)
        version = BusinessPartnerVersionModel(
            business_partner_id=partner.id,
            version="1.0.0",
            status="ACTIVE",
            legal_name=partner.legal_name,
            trade_name=partner.trade_name,
            person_type=partner.person_type,
            snapshot_data=snap_res["snapshot_data"],
            content_hash=snap_res["content_hash"],
            created_by=actor_id,
        )
        self.db.add(version)
        self.db.flush()

        partner.active_version_id = version.id
        self.db.commit()
        self.db.refresh(partner)

        self._write_audit(
            event_code="logistics.business_partner.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=partner.id,
            details={"partner_code": partner.partner_code, "legal_name": partner.legal_name},
        )
        return partner

    def get_partner(self, partner_id: UUID, organization_id: UUID) -> BusinessPartnerModel:
        partner = self.db.get(BusinessPartnerModel, partner_id)
        if not partner or partner.organization_id != organization_id:
            raise HTTPException(status_code=404, detail=f"Partner {partner_id} not found")
        return partner

    def activate_partner(self, partner_id: UUID, organization_id: UUID, actor_id: UUID | None = None) -> BusinessPartnerModel:
        partner = self.get_partner(partner_id, organization_id)
        if partner.status == "ACTIVE":
            return partner
        if partner.status == "BLOCKED":
            raise HTTPException(status_code=409, detail="Cannot activate a BLOCKED partner. Unblock first.")

        partner.status = "ACTIVE"
        partner.updated_by = actor_id
        partner.row_version += 1

        # Resolve compliance
        comp_res = BusinessPartnerComplianceResolver.resolve_compliance(self.db, partner_id)
        partner.compliance_status = comp_res["compliance_status"]
        partner.risk_status = comp_res["risk_status"]

        self.db.commit()
        self.db.refresh(partner)

        self._write_audit(
            event_code="logistics.business_partner.activated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=partner.id,
            details={"status": partner.status},
        )
        return partner

    def block_partner(self, partner_id: UUID, organization_id: UUID, actor_id: UUID | None = None, reason: str | None = None) -> BusinessPartnerModel:
        partner = self.get_partner(partner_id, organization_id)
        partner.status = "BLOCKED"
        partner.updated_by = actor_id
        partner.row_version += 1
        self.db.commit()
        self.db.refresh(partner)

        self._write_audit(
            event_code="logistics.business_partner.blocked",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=partner.id,
            details={"reason": reason},
        )
        return partner

    def add_role(self, partner_id: UUID, organization_id: UUID, role_type: str, actor_id: UUID | None = None) -> BusinessPartnerRoleModel:
        partner = self.get_partner(partner_id, organization_id)
        r_upper = role_type.upper()

        existing = self.db.scalars(
            select(BusinessPartnerRoleModel).where(
                and_(
                    BusinessPartnerRoleModel.business_partner_id == partner_id,
                    BusinessPartnerRoleModel.role_type == r_upper,
                )
            )
        ).first()

        if existing:
            if existing.status == "ACTIVE":
                return existing
            existing.status = "ACTIVE"
            existing.updated_by = actor_id
            self.db.commit()
            return existing

        role = BusinessPartnerRoleModel(
            business_partner_id=partner.id,
            role_type=r_upper,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(role)
        self.db.flush()

        if r_upper == "SUPPLIER":
            self.db.add(SupplierProfileModel(business_partner_role_id=role.id))
        elif r_upper == "CUSTOMER":
            self.db.add(CustomerProfileModel(business_partner_role_id=role.id))
        elif r_upper == "CARRIER":
            self.db.add(CarrierProfileModel(business_partner_role_id=role.id))

        self.db.commit()
        self.db.refresh(role)

        self._write_audit(
            event_code="logistics.business_partner_role.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=role.id,
            details={"role_type": r_upper},
        )
        return role

    def add_address(
        self,
        partner_id: UUID,
        organization_id: UUID,
        address_line_1: str,
        address_type: str = "FISCAL",
        district: str | None = None,
        province: str | None = None,
        department: str | None = None,
        is_primary: bool = True,
        actor_id: UUID | None = None,
    ) -> BusinessPartnerAddressModel:
        partner = self.get_partner(partner_id, organization_id)
        if is_primary:
            # reset other primary addresses of same type
            self.db.execute(
                update(BusinessPartnerAddressModel)
                .where(
                    and_(
                        BusinessPartnerAddressModel.business_partner_id == partner_id,
                        BusinessPartnerAddressModel.address_type == address_type.upper(),
                    )
                )
                .values(is_primary=False)
            )

        addr = BusinessPartnerAddressModel(
            business_partner_id=partner.id,
            address_type=address_type.upper(),
            address_line_1=address_line_1,
            district=district,
            province=province,
            department=department,
            is_primary=is_primary,
            created_by=actor_id,
        )
        self.db.add(addr)
        self.db.commit()
        self.db.refresh(addr)
        return addr

    def add_contact(
        self,
        partner_id: UUID,
        organization_id: UUID,
        full_name: str,
        contact_type: str = "GENERAL",
        email: str | None = None,
        phone: str | None = None,
        is_primary: bool = True,
        actor_id: UUID | None = None,
    ) -> BusinessPartnerContactModel:
        partner = self.get_partner(partner_id, organization_id)
        if is_primary:
            self.db.execute(
                update(BusinessPartnerContactModel)
                .where(BusinessPartnerContactModel.business_partner_id == partner_id)
                .values(is_primary=False)
            )

        contact = BusinessPartnerContactModel(
            business_partner_id=partner.id,
            contact_type=contact_type.upper(),
            full_name=full_name,
            email=email,
            phone=phone,
            is_primary=is_primary,
            created_by=actor_id,
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def submit_evaluation(
        self,
        partner_id: UUID,
        organization_id: UUID,
        role_type: str,
        criteria_scores: List[Dict[str, Any]],
        summary: str | None = None,
        actor_id: UUID | None = None,
    ) -> BusinessPartnerEvaluationModel:
        partner = self.get_partner(partner_id, organization_id)

        total_score = Decimal("0.00")
        total_weight = Decimal("0.00")

        criteria_objects = []
        for c in criteria_scores:
            weight = Decimal(str(c.get("weight", "0.0")))
            score = Decimal(str(c.get("score", "0.0")))
            weighted = (weight * score) / Decimal("100.00")

            total_weight += weight
            total_score += weighted

            criteria_objects.append(
                BusinessPartnerEvaluationCriterionModel(
                    criterion_code=c.get("code", "CRIT"),
                    criterion_name=c.get("name", "Criterion"),
                    weight=weight,
                    score=score,
                    weighted_score=weighted,
                    observations=c.get("observations"),
                )
            )

        risk_level = "LOW"
        if total_score < Decimal("50.00"):
            risk_level = "HIGH"
        elif total_score < Decimal("75.00"):
            risk_level = "MEDIUM"

        evaluation = BusinessPartnerEvaluationModel(
            business_partner_id=partner.id,
            role_type=role_type.upper(),
            total_score=total_score,
            risk_level=risk_level,
            status="APPROVED",
            summary=summary,
            evaluator_user_id=actor_id,
            approved_by=actor_id,
            approved_at=utc_now(),
        )
        self.db.add(evaluation)
        self.db.flush()

        for crit in criteria_objects:
            crit.evaluation_id = evaluation.id
            self.db.add(crit)

        partner.risk_status = risk_level
        self.db.commit()
        self.db.refresh(evaluation)

        self._write_audit(
            event_code="logistics.business_partner_evaluation.approved",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=evaluation.id,
            details={"total_score": str(total_score), "risk_level": risk_level},
        )
        return evaluation
