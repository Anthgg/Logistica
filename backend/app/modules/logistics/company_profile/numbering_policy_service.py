"""Service for numbering display policies (Phase 021)."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.company_profile.models import OrganizationNumberingDisplayPolicyModel
from app.modules.logistics.company_profile.schemas import (
    NumberingDisplayPolicyCreate,
    NumberingDisplayPolicyUpdate,
)
from app.modules.logistics.company_profile.validators import validate_numbering_display_pattern


class NumberingPolicyService:
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

    def list_policies(self, organization_id: UUID) -> list[OrganizationNumberingDisplayPolicyModel]:
        return self.db.scalars(
            select(OrganizationNumberingDisplayPolicyModel)
            .where(OrganizationNumberingDisplayPolicyModel.organization_id == organization_id)
            .order_by(OrganizationNumberingDisplayPolicyModel.created_at.desc())
        ).all()

    def get_policy(self, organization_id: UUID, policy_id: UUID) -> OrganizationNumberingDisplayPolicyModel | None:
        pol = self.db.get(OrganizationNumberingDisplayPolicyModel, policy_id)
        if pol and pol.organization_id == organization_id:
            return pol
        return None

    def create_policy(
        self, organization_id: UUID, req: NumberingDisplayPolicyCreate, actor_id: UUID | None = None
    ) -> OrganizationNumberingDisplayPolicyModel:
        is_valid, msg = validate_numbering_display_pattern(req.display_pattern, req.sequence_padding)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        policy = OrganizationNumberingDisplayPolicyModel(
            organization_id=organization_id,
            branch_id=req.branch_id,
            document_type_id=req.document_type_id,
            code_standard_version=req.code_standard_version,
            document_site_code_id=req.document_site_code_id,
            display_pattern=req.display_pattern,
            sequence_padding=req.sequence_padding,
            show_internal_code=req.show_internal_code,
            show_external_series=req.show_external_series,
            show_external_number=req.show_external_number,
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(policy)
        self.db.flush()

        self._write_audit(
            event_code="logistics.numbering_policy.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_numbering_display_policies",
            resource_id=policy.id,
            details={"display_pattern": policy.display_pattern, "sequence_padding": policy.sequence_padding},
        )

        return policy

    def update_policy(
        self, organization_id: UUID, policy_id: UUID, req: NumberingDisplayPolicyUpdate, actor_id: UUID | None = None
    ) -> OrganizationNumberingDisplayPolicyModel:
        pol = self.get_policy(organization_id, policy_id)
        if not pol:
            raise HTTPException(status_code=404, detail="OrganizationNumberingDisplayPolicy not found.")

        pattern = req.display_pattern or pol.display_pattern
        padding = req.sequence_padding if req.sequence_padding is not None else pol.sequence_padding

        is_valid, msg = validate_numbering_display_pattern(pattern, padding)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        if req.branch_id is not None:
            pol.branch_id = req.branch_id
        if req.document_site_code_id is not None:
            pol.document_site_code_id = req.document_site_code_id
        if req.display_pattern is not None:
            pol.display_pattern = req.display_pattern
        if req.sequence_padding is not None:
            pol.sequence_padding = req.sequence_padding
        if req.show_internal_code is not None:
            pol.show_internal_code = req.show_internal_code
        if req.show_external_series is not None:
            pol.show_external_series = req.show_external_series
        if req.show_external_number is not None:
            pol.show_external_number = req.show_external_number

        pol.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.numbering_policy.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_numbering_display_policies",
            resource_id=pol.id,
            details={"display_pattern": pol.display_pattern},
        )

        return pol

    def preview_numbering_display(
        self,
        organization_id: UUID,
        doc_type_code: str,
        site_code: str = "LIM",
        sample_year: int = 2026,
        sample_sequence: int = 15,
        display_pattern: str = "{TYPE}-{SITE}-{YEAR}-{SEQUENCE}",
        sequence_padding: int = 6,
        external_series: str = "F001",
        external_number: int = 124,
    ) -> dict[str, str]:
        """Renders sample formatted codes for UI preview without reserving numbers or mutating DB."""
        is_valid, msg = validate_numbering_display_pattern(display_pattern, sequence_padding)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        seq_str = str(sample_sequence).zfill(sequence_padding)
        formatted_internal = (
            display_pattern.replace("{TYPE}", doc_type_code.upper())
            .replace("{SITE}", site_code.upper())
            .replace("{YEAR}", str(sample_year))
            .replace("{SEQUENCE}", seq_str)
            .replace("{EXTERNAL_SERIES}", external_series)
            .replace("{EXTERNAL_NUMBER}", str(external_number).zfill(8))
        )

        formatted_external = f"{external_series}-{str(external_number).zfill(8)}"

        return {
            "formatted_internal_code": formatted_internal,
            "formatted_external_code": formatted_external,
            "sample_sequence_used": seq_str,
            "notice": "VISTA PREVIA — No se ha reservado ni incrementado ninguna secuencia.",
        }
