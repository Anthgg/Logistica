"""FileAsset application service for Phase 030."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.domain.errors.exceptions import (
    FileAccessDeniedError,
    FileLegalHoldActiveError,
    FileNotFoundError,
    FileVersionNotFoundError,
)
from app.modules.logistics.files.domain.services.services import (
    FileAccessPolicyService,
    FileHashService,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    FileAssetType,
    FileClassification,
    FileLifecycleStatus,
    FileVersionStatus,
    LegalHoldStatus,
)
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileLegalHoldModel,
    FileVersionModel,
)
from app.modules.logistics.files.infrastructure.storage.storage_gateway import (
    get_storage_gateway,
)


class FileAssetService:
    """Core CRUD, versioning, archive and history operations for FileAssets."""

    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_gateway()

    def get_file_asset(self, file_id: UUID, organization_id: UUID) -> FileAssetModel:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))
        return asset

    def list_file_assets(
        self,
        organization_id: UUID,
        asset_type: Optional[str] = None,
        classification: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[FileAssetModel], int]:
        stmt = select(FileAssetModel).where(FileAssetModel.organization_id == organization_id)
        
        if asset_type:
            stmt = stmt.where(FileAssetModel.asset_type == asset_type)
        if classification:
            stmt = stmt.where(FileAssetModel.classification == classification)
        if lifecycle_status:
            stmt = stmt.where(FileAssetModel.lifecycle_status == lifecycle_status)
        if search_query:
            stmt = stmt.where(
                (FileAssetModel.title.ilike(f"%{search_query}%"))
                | (FileAssetModel.file_code.ilike(f"%{search_query}%"))
            )

        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(FileAssetModel.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def update_file_asset_metadata(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        classification: Optional[FileClassification] = None,
        correlation_id: Optional[str] = None,
    ) -> FileAssetModel:
        asset = self.get_file_asset(file_id, organization_id)
        
        if title:
            asset.title = title
        if description is not None:
            asset.description = description
        if classification:
            asset.classification = classification.value
        
        asset.updated_by = user_id
        asset.row_version += 1

        self.db.commit()
        self.db.refresh(asset)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.metadata_updated",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_asset",
                resource_id=str(file_id),
                correlation_id=correlation_id or str(file_id),
                payload={"title": asset.title, "classification": asset.classification},
            ),
        )
        return asset

    def archive_file_asset(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
        correlation_id: Optional[str] = None,
    ) -> FileAssetModel:
        asset = self.get_file_asset(file_id, organization_id)
        
        # Check active legal hold
        active_hold = self.db.execute(
            select(FileLegalHoldModel).where(
                FileLegalHoldModel.file_asset_id == file_id,
                FileLegalHoldModel.status == LegalHoldStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        if active_hold:
            raise FileLegalHoldActiveError(str(file_id))

        asset.lifecycle_status = FileLifecycleStatus.ARCHIVED.value
        asset.archived_at = datetime.now(timezone.utc)
        asset.archived_by = user_id
        asset.archive_reason = reason
        asset.updated_by = user_id
        asset.row_version += 1

        self.db.commit()
        self.db.refresh(asset)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.archived",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_asset",
                resource_id=str(file_id),
                correlation_id=correlation_id or str(file_id),
                payload={"reason": reason},
            ),
        )
        return asset

    def restore_file_asset(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        correlation_id: Optional[str] = None,
    ) -> FileAssetModel:
        asset = self.get_file_asset(file_id, organization_id)
        
        asset.lifecycle_status = FileLifecycleStatus.AVAILABLE.value
        asset.archived_at = None
        asset.archived_by = None
        asset.archive_reason = None
        asset.updated_by = user_id
        asset.row_version += 1

        self.db.commit()
        self.db.refresh(asset)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.restored",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_asset",
                resource_id=str(file_id),
                correlation_id=correlation_id or str(file_id),
            ),
        )
        return asset

    def get_file_versions(
        self, file_id: UUID, organization_id: UUID
    ) -> List[FileVersionModel]:
        asset = self.get_file_asset(file_id, organization_id)
        stmt = (
            select(FileVersionModel)
            .where(FileVersionModel.file_asset_id == asset.id)
            .order_by(FileVersionModel.version_number.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
