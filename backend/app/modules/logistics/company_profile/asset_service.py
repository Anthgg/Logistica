"""Service for managing institutional assets (Logos, Signatures) (Phase 021)."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.company_profile.models import OrganizationAssetModel
from app.modules.logistics.company_profile.validators import validate_and_sanitize_image
from app.modules.logistics.documents.infrastructure.storage import DocumentArtifactStorage


class AssetService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = DocumentArtifactStorage()

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

    def list_assets(self, organization_id: UUID) -> list[OrganizationAssetModel]:
        return self.db.scalars(
            select(OrganizationAssetModel)
            .where(OrganizationAssetModel.organization_id == organization_id)
            .order_by(OrganizationAssetModel.uploaded_at.desc())
        ).all()

    def get_asset(self, organization_id: UUID, asset_id: UUID) -> OrganizationAssetModel | None:
        asset = self.db.get(OrganizationAssetModel, asset_id)
        if asset and asset.organization_id == organization_id:
            return asset
        return None

    def get_asset_content(self, organization_id: UUID, asset_id: UUID) -> tuple[bytes, str, str]:
        asset = self.get_asset(organization_id, asset_id)
        if not asset or asset.status not in ("ACTIVE", "INACTIVE"):
            raise HTTPException(status_code=404, detail="OrganizationAsset not found or revoked.")

        content = self.storage.get(asset.storage_key)
        return content, asset.mime_type, asset.filename

    def upload_asset(
        self,
        organization_id: UUID,
        file_bytes: bytes,
        filename: str,
        asset_type: str,
        actor_id: UUID | None = None,
    ) -> OrganizationAssetModel:
        asset_type = asset_type.upper()
        if asset_type not in (
            "PRIMARY_LOGO", "MONOCHROME_LOGO", "DOCUMENT_LOGO",
            "VISUAL_SIGNATURE", "OFFICIAL_STAMP", "DOCUMENT_BACKGROUND"
        ):
            raise HTTPException(status_code=400, detail=f"Asset type '{asset_type}' no soportado.")

        try:
            val_res = validate_and_sanitize_image(
                image_bytes=file_bytes,
                filename=filename,
                asset_type=asset_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        sanitized_bytes = val_res["sanitized_bytes"]
        file_hash = val_res["file_hash"]

        # Calculate version
        existing_count = self.db.scalars(
            select(OrganizationAssetModel).where(
                and_(
                    OrganizationAssetModel.organization_id == organization_id,
                    OrganizationAssetModel.asset_type == asset_type,
                )
            )
        ).all()

        next_version = len(existing_count) + 1
        storage_key = f"companies/{organization_id}/assets/{asset_type.lower()}_v{next_version}_{file_hash[:8]}.png"

        self.storage.put(storage_key, sanitized_bytes)

        asset = OrganizationAssetModel(
            organization_id=organization_id,
            asset_type=asset_type,
            filename=val_res["filename"],
            mime_type=val_res["mime_type"],
            size_bytes=val_res["size_bytes"],
            width=val_res["width"],
            height=val_res["height"],
            file_hash=file_hash,
            storage_provider=settings.STORAGE_PROVIDER,
            storage_key=storage_key,
            status="ACTIVE",
            version=next_version,
            uploaded_by=actor_id,
            uploaded_at=utc_now(),
        )
        self.db.add(asset)
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_asset.uploaded",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_assets",
            resource_id=asset.id,
            details={"asset_type": asset_type, "file_hash": file_hash[:16], "version": next_version},
        )

        return asset

    def activate_asset(self, organization_id: UUID, asset_id: UUID, actor_id: UUID | None = None) -> OrganizationAssetModel:
        asset = self.get_asset(organization_id, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="OrganizationAsset not found.")

        asset.status = "ACTIVE"
        asset.approved_by = actor_id
        asset.approved_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_asset.activated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_assets",
            resource_id=asset.id,
            details={"asset_type": asset.asset_type},
        )

        return asset

    def revoke_asset(self, organization_id: UUID, asset_id: UUID, actor_id: UUID | None = None) -> OrganizationAssetModel:
        asset = self.get_asset(organization_id, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="OrganizationAsset not found.")

        asset.status = "REVOKED"
        asset.revoked_at = utc_now()
        self.db.flush()

        self._write_audit(
            event_code="logistics.company_asset.revoked",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_type="organization_assets",
            resource_id=asset.id,
            details={"asset_type": asset.asset_type},
        )

        return asset
