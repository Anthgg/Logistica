"""Service for authorized signers and visual signature resolution (Phase 021)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.company_profile.models import AuthorizedSignerModel, OrganizationAssetModel
from app.modules.logistics.company_profile.schemas import (
    AuthorizedSignerCreate,
    AuthorizedSignerUpdate,
)


class SignerService:
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

    def list_signers(self, organization_id: UUID) -> list[AuthorizedSignerModel]:
        return self.db.scalars(
            select(AuthorizedSignerModel)
            .where(AuthorizedSignerModel.organization_id == organization_id)
            .order_by(AuthorizedSignerModel.created_at.desc())
        ).all()

    def get_signer(self, organization_id: UUID, signer_id: UUID) -> AuthorizedSignerModel | None:
        signer = self.db.get(AuthorizedSignerModel, signer_id)
        if signer and signer.organization_id == organization_id:
            return signer
        return None

    def create_signer(
        self, organization_id: UUID, req: AuthorizedSignerCreate, actor_id: UUID | None = None
    ) -> AuthorizedSignerModel:
        now = utc_now()

        signer = AuthorizedSignerModel(
            organization_id=organization_id,
            user_id=req.user_id,
            full_name=req.full_name,
            position_title=req.position_title,
            department=req.department,
            document_number_masked=req.document_number_masked,
            authorization_reference=req.authorization_reference,
            authorization_type=req.authorization_type.upper(),
            valid_from=req.valid_from or now,
            valid_until=req.valid_until,
            status="ACTIVE",
            signature_asset_id=req.signature_asset_id,
            stamp_asset_id=req.stamp_asset_id,
            can_sign_all_branches=req.can_sign_all_branches,
            branch_scope=[str(b) for b in req.branch_scope] if req.branch_scope else None,
            document_family_scope=[f.upper() for f in req.document_family_scope] if req.document_family_scope else None,
            document_type_scope=[t.upper() for t in req.document_type_scope] if req.document_type_scope else None,
            max_amount=req.max_amount,
            currency_code=req.currency_code.upper() if req.currency_code else None,
            notes=req.notes,
            created_by=actor_id,
        )
        self.db.add(signer)
        self.db.flush()

        self._write_audit(
            event_code="logistics.authorized_signer.created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="authorized_signers",
            resource_id=signer.id,
            details={"full_name": signer.full_name, "position_title": signer.position_title},
        )

        return signer

    def update_signer(
        self, organization_id: UUID, signer_id: UUID, req: AuthorizedSignerUpdate, actor_id: UUID | None = None
    ) -> AuthorizedSignerModel:
        signer = self.get_signer(organization_id, signer_id)
        if not signer:
            raise HTTPException(status_code=404, detail="AuthorizedSigner not found.")

        for field in [
            "full_name", "position_title", "department", "document_number_masked",
            "authorization_reference", "valid_from", "valid_until", "signature_asset_id",
            "stamp_asset_id", "can_sign_all_branches", "max_amount", "notes"
        ]:
            val = getattr(req, field, None)
            if val is not None:
                setattr(signer, field, val)

        if req.authorization_type is not None:
            signer.authorization_type = req.authorization_type.upper()
        if req.currency_code is not None:
            signer.currency_code = req.currency_code.upper()
        if req.branch_scope is not None:
            signer.branch_scope = [str(b) for b in req.branch_scope]
        if req.document_family_scope is not None:
            signer.document_family_scope = [f.upper() for f in req.document_family_scope]
        if req.document_type_scope is not None:
            signer.document_type_scope = [t.upper() for t in req.document_type_scope]

        signer.updated_by = actor_id
        signer.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.authorized_signer.updated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="authorized_signers",
            resource_id=signer.id,
            details={"full_name": signer.full_name},
        )

        return signer

    def set_signer_status(
        self,
        organization_id: UUID,
        signer_id: UUID,
        status: str,
        reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> AuthorizedSignerModel:
        signer = self.get_signer(organization_id, signer_id)
        if not signer:
            raise HTTPException(status_code=404, detail="AuthorizedSigner not found.")

        status = status.upper()
        if status == "REVOKED" and not reason:
            raise HTTPException(status_code=400, detail="Revocar un firmante requiere especificar un motivo.")

        signer.status = status
        signer.updated_by = actor_id
        signer.updated_at = utc_now()

        event_type = "logistics.authorized_signer.updated"
        if status == "ACTIVE":
            signer.approved_by = actor_id
            signer.approved_at = utc_now()
            event_type = "logistics.authorized_signer.activated"
        elif status == "SUSPENDED":
            event_type = "logistics.authorized_signer.suspended"
        elif status == "REVOKED":
            signer.revoked_by = actor_id
            signer.revoked_at = utc_now()
            signer.revocation_reason = reason
            event_type = "logistics.authorized_signer.revoked"

        self.db.flush()

        self._write_audit(
            event_code=event_type,
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="authorized_signers",
            resource_id=signer.id,
            details={"status": status, "reason": reason},
        )

        return signer

    def resolve_authorized_signer(
        self,
        organization_id: UUID,
        branch_id: UUID | None,
        document_family: str,
        document_type_code: str,
        amount: Decimal | None = None,
        currency_code: str | None = None,
        requested_signer_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Resolves an authorized signer for document emission."""
        now = utc_now()

        query = select(AuthorizedSignerModel).where(
            and_(
                AuthorizedSignerModel.organization_id == organization_id,
                AuthorizedSignerModel.status == "ACTIVE",
                AuthorizedSignerModel.valid_from <= now,
                or_(AuthorizedSignerModel.valid_until.is_(None), AuthorizedSignerModel.valid_until >= now),
            )
        )

        if requested_signer_id:
            query = query.where(AuthorizedSignerModel.id == requested_signer_id)

        signers = self.db.scalars(query).all()
        warnings = []

        valid_signer = None
        for s in signers:
            # Check branch scope
            if not s.can_sign_all_branches and branch_id:
                if s.branch_scope and str(branch_id) not in s.branch_scope:
                    warnings.append(f"Firmante '{s.full_name}' no tiene alcance en la sede especificada.")
                    continue

            # Check family scope
            if s.document_family_scope and document_family.upper() not in s.document_family_scope:
                warnings.append(f"Firmante '{s.full_name}' no tiene alcance en la familia '{document_family}'.")
                continue

            # Check type scope
            if s.document_type_scope and document_type_code.upper() not in s.document_type_scope:
                warnings.append(f"Firmante '{s.full_name}' no tiene alcance en el tipo '{document_type_code}'.")
                continue

            # Check amount limit
            if amount and s.max_amount:
                if amount > s.max_amount:
                    warnings.append(f"Monto de documento ({amount}) excede el límite autorizado del firmante ({s.max_amount}).")
                    continue

            valid_signer = s
            break

        if not valid_signer:
            return {
                "signer": None,
                "authorization_status": "NO_AUTHORIZED_SIGNER",
                "signature_asset": None,
                "warnings": warnings or ["No se encontró ningún firmante activo y autorizado para este alcance."],
            }

        # Resolve signature asset metadata
        sig_asset = None
        if valid_signer.signature_asset_id:
            asset = self.db.get(OrganizationAssetModel, valid_signer.signature_asset_id)
            if asset and asset.status == "ACTIVE":
                sig_asset = {
                    "asset_id": str(asset.id),
                    "filename": asset.filename,
                    "file_hash": asset.file_hash,
                    "mime_type": asset.mime_type,
                }

        return {
            "signer": {
                "id": str(valid_signer.id),
                "full_name": valid_signer.full_name,
                "position_title": valid_signer.position_title,
                "department": valid_signer.department,
                "authorization_type": valid_signer.authorization_type,
                "document_number_masked": valid_signer.document_number_masked,
            },
            "authorization_status": "AUTHORIZED",
            "signature_asset": sig_asset,
            "warnings": [],
        }
