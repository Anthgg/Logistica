"""RucAssistedVerificationService & BusinessPartnerRucIntegrationService (Phase 026)."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.partners.models import (
    BusinessPartnerAddressModel,
    BusinessPartnerIdentifierModel,
    BusinessPartnerModel,
    BusinessPartnerVersionModel,
)
from app.modules.logistics.partners.partner_service import BusinessPartnerService
from app.modules.logistics.partners.snapshot_provider import BusinessPartnerSnapshotProvider
from app.modules.logistics.ruc.domain.value_objects.enums import ConfidenceLevel, RucSourceType
from app.modules.logistics.ruc.infrastructure.persistence.models import (
    BusinessPartnerRucVerificationModel,
    RucAssistedVerificationModel,
    RucDataConflictModel,
)


class RucAssistedVerificationService:
    """Manages official manual assisted verification workflow."""

    def __init__(self, db: Session):
        self.db = db

    def create_assisted_verification(
        self,
        organization_id: UUID,
        ruc: str,
        verification_reason: str,
        source_reference: str,
        actor_id: UUID,
        business_partner_id: Optional[UUID] = None,
        observed_legal_name: Optional[str] = None,
        observed_status: Optional[str] = None,
        observed_condition: Optional[str] = None,
        observed_ubigeo: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> RucAssistedVerificationModel:
        record = RucAssistedVerificationModel(
            id=uuid4(),
            organization_id=organization_id,
            business_partner_id=business_partner_id,
            ruc=ruc,
            verification_reason=verification_reason,
            source_type="ASSISTED_OFFICIAL_REVIEW",
            source_reference=source_reference,
            reviewed_at=utc_now(),
            reviewed_by=actor_id,
            observed_legal_name=observed_legal_name,
            observed_status=observed_status,
            observed_condition=observed_condition,
            observed_ubigeo=observed_ubigeo,
            observations=observations,
            result="MATCH_CONFIRMED",
            confidence_level="MEDIUM",
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.assisted_verification_created",
                category="INTEGRATION",
                severity="MEDIUM",
                description=f"Verificación asistida creada para RUC {ruc}",
                actor_user_id=actor_id,
            ),
        )

        return record

    def approve_assisted_verification(self, verification_id: UUID, organization_id: UUID, approver_id: UUID) -> RucAssistedVerificationModel:
        record = self.db.scalars(
            select(RucAssistedVerificationModel).where(
                and_(
                    RucAssistedVerificationModel.id == verification_id,
                    RucAssistedVerificationModel.organization_id == organization_id,
                )
            )
        ).first()

        if not record:
            raise HTTPException(status_code=404, detail="Verificación asistida no encontrada.")

        record.approved_by = approver_id
        record.approved_at = utc_now()
        record.confidence_level = "HIGH"
        self.db.commit()

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.assisted_verification_approved",
                category="INTEGRATION",
                severity="HIGH",
                description=f"Verificación asistida aprobada para RUC {record.ruc}",
                actor_user_id=approver_id,
            ),
        )

        return record


class BusinessPartnerRucIntegrationService:
    """Manages BusinessPartner RUC verification and controlled field-by-field application."""

    def __init__(self, db: Session):
        self.db = db

    def verify_partner_ruc(
        self,
        organization_id: UUID,
        partner_id: UUID,
        lookup_result: Dict[str, Any],
        actor_id: Optional[UUID] = None,
    ) -> BusinessPartnerRucVerificationModel:
        partner_service = BusinessPartnerService(self.db)
        partner = partner_service.get_partner(partner_id, organization_id)

        ident = self.db.scalars(
            select(BusinessPartnerIdentifierModel).where(
                and_(
                    BusinessPartnerIdentifierModel.business_partner_id == partner.id,
                    BusinessPartnerIdentifierModel.identifier_type == "RUC",
                )
            )
        ).first()

        # Mark previous verifications SUPERSEDED
        existing = self.db.scalars(
            select(BusinessPartnerRucVerificationModel).where(
                and_(
                    BusinessPartnerRucVerificationModel.business_partner_id == partner.id,
                    BusinessPartnerRucVerificationModel.status == "CURRENT",
                )
            )
        ).all()
        for ex in existing:
            ex.status = "SUPERSEDED"

        snapshot_hash = BusinessPartnerSnapshotProvider.calculate_content_hash(lookup_result)

        verification = BusinessPartnerRucVerificationModel(
            id=uuid4(),
            organization_id=organization_id,
            business_partner_id=partner.id,
            identifier_id=ident.id if ident else None,
            ruc=lookup_result["normalized_ruc"],
            verification_method="OFFICIAL_REGISTRY" if lookup_result["source"] == "SUNAT_REDUCED_REGISTRY" else "AUTHORIZED_PROVIDER",
            source=lookup_result["source"],
            dataset_version_id=UUID(lookup_result["dataset_version_id"]) if lookup_result["dataset_version_id"] != "NONE" else None,
            verification_result="VERIFIED",
            verified_legal_name=lookup_result["legal_name"],
            verified_taxpayer_status=lookup_result["taxpayer_status"],
            verified_domicile_condition=lookup_result["domicile_condition"],
            verified_ubigeo=lookup_result["ubigeo_code"],
            source_date=datetime.fromisoformat(lookup_result["source_published_at"]) if lookup_result.get("source_published_at") else None,
            verified_at=utc_now(),
            verified_by=actor_id,
            confidence_level=lookup_result["confidence_level"],
            snapshot_payload=lookup_result,
            snapshot_hash=snapshot_hash,
            status="CURRENT",
        )
        self.db.add(verification)

        # Update Identifier status ONLY — do NOT change legal_name automatically
        if ident:
            ident.verification_status = "VERIFIED_EXTERNAL"
            ident.verified_at = utc_now()
            ident.verification_source = lookup_result["source"]

        self.db.commit()
        self.db.refresh(verification)

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.business_partner.ruc_verified",
                category="MASTER_DATA",
                severity="HIGH",
                description=f"Verificación de RUC registrada para socio {partner.partner_code}",
                actor_user_id=actor_id,
                payload={"partner_id": str(partner.id), "ruc": lookup_result["normalized_ruc"]},
            ),
        )

        return verification

    def apply_verified_fields_to_partner(
        self,
        organization_id: UUID,
        partner_id: UUID,
        verification_id: UUID,
        apply_legal_name: bool = False,
        apply_annex_as_candidate: bool = False,
        selected_annex_address: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> BusinessPartnerModel:
        """Controlled field-by-field application of verified RUC data.

        Does NOT activate or block partner automatically.
        Does NOT replace primary address silently.
        Creates a new BusinessPartnerVersion.
        """
        partner_service = BusinessPartnerService(self.db)
        partner = partner_service.get_partner(partner_id, organization_id)

        verif = self.db.get(BusinessPartnerRucVerificationModel, verification_id)
        if not verif or verif.business_partner_id != partner.id:
            raise HTTPException(status_code=404, detail="Registro de verificación no encontrado.")

        changes = {}

        if apply_legal_name and verif.verified_legal_name:
            if partner.legal_name != verif.verified_legal_name:
                changes["legal_name"] = (partner.legal_name, verif.verified_legal_name)
                partner.legal_name = verif.verified_legal_name

        if apply_annex_as_candidate and selected_annex_address:
            # Add annex address as non-primary REGISTERED address candidate
            partner_service.add_address(
                partner_id=partner.id,
                organization_id=organization_id,
                address_line_1=selected_annex_address,
                address_type="REGISTERED",
                is_primary=False,
                actor_id=actor_id,
            )
            changes["added_annex_address"] = selected_annex_address

        if changes:
            partner.row_version += 1
            partner.updated_at = utc_now()
            partner.updated_by = actor_id

            # Create new version snapshot
            snapshot_dict = BusinessPartnerSnapshotProvider.build_snapshot_dict(partner, self.db)
            chash = BusinessPartnerSnapshotProvider.calculate_content_hash(snapshot_dict)

            if partner.active_version_id:
                previous_version = self.db.get(
                    BusinessPartnerVersionModel,
                    partner.active_version_id,
                )
                if previous_version:
                    previous_version.status = "SUPERSEDED"
                    previous_version.effective_to = utc_now()

            new_ver = BusinessPartnerVersionModel(
                id=uuid4(),
                business_partner_id=partner.id,
                version=f"1.0.{partner.row_version}",
                status="ACTIVE",
                legal_name=partner.legal_name,
                trade_name=partner.trade_name,
                person_type=partner.person_type,
                content_hash=chash,
                snapshot_data=snapshot_dict,
                created_by=actor_id,
            )
            self.db.add(new_ver)
            self.db.flush()
            partner.active_version_id = new_ver.id
            self.db.commit()

            audit_service.log_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.business_partner.ruc_data_applied",
                    category="MASTER_DATA",
                    severity="HIGH",
                    description=f"Datos verificados de RUC aplicados a socio {partner.partner_code}",
                    actor_user_id=actor_id,
                    payload={"changes": changes, "reason": reason},
                ),
            )

        return partner
