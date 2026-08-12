"""Preview and Download application service for Phase 030."""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.domain.errors.exceptions import (
    FileAccessDeniedError,
    FileDownloadNotAvailableError,
    FileNotFoundError,
    FilePreviewNotAvailableError,
    FileQuarantinedError,
)
from app.modules.logistics.files.domain.services.services import (
    FileAccessPolicyService,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    FileLifecycleStatus,
)
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileVersionModel,
)
from app.modules.logistics.files.infrastructure.storage.storage_gateway import (
    SignedAccessUrl,
    get_storage_gateway,
)


class FilePreviewDownloadService:
    """Handles secure file streaming, preview generation and signed access URLs."""

    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_gateway()

    def get_download_access(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        version_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[SignedAccessUrl, FileAssetModel, FileVersionModel]:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))

        if asset.lifecycle_status == FileLifecycleStatus.QUARANTINED.value:
            raise FileQuarantinedError(str(file_id))

        if asset.lifecycle_status in (FileLifecycleStatus.DELETED.value, FileLifecycleStatus.REJECTED.value):
            raise FileDownloadNotAvailableError(str(file_id), f"El archivo está en estado '{asset.lifecycle_status}'.")

        FileAccessPolicyService.check_access(asset, user_id, organization_id, required_action="DOWNLOAD")

        ver_id = version_id or asset.current_version_id
        version = self.db.execute(
            select(FileVersionModel).where(FileVersionModel.id == ver_id)
        ).scalar_one_or_none()
        if not version:
            raise FileNotFoundError(f"Versión {ver_id} no encontrada.")

        signed_url = self.storage.generate_download_url(
            bucket=version.bucket_reference,
            object_key=version.object_key,
            filename=version.sanitized_filename,
            content_type=version.detected_MIME_type,
            expires_in_seconds=900,
        )

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.downloaded",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_asset",
                resource_id=str(file_id),
                correlation_id=correlation_id or str(file_id),
                payload={"version_id": str(version.id), "filename": version.sanitized_filename},
            ),
        )
        return signed_url, asset, version

    def get_preview_access(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        version_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[SignedAccessUrl, FileAssetModel, FileVersionModel]:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))

        if asset.lifecycle_status == FileLifecycleStatus.QUARANTINED.value:
            raise FileQuarantinedError(str(file_id))

        FileAccessPolicyService.check_access(asset, user_id, organization_id, required_action="PREVIEW")

        ver_id = version_id or asset.current_version_id
        version = self.db.execute(
            select(FileVersionModel).where(FileVersionModel.id == ver_id)
        ).scalar_one_or_none()
        if not version:
            raise FileNotFoundError(f"Versión {ver_id} no encontrada.")

        signed_url = self.storage.generate_preview_url(
            bucket=version.bucket_reference,
            object_key=version.object_key,
            content_type=version.detected_MIME_type,
            expires_in_seconds=600,
        )

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.previewed",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_asset",
                resource_id=str(file_id),
                correlation_id=correlation_id or str(file_id),
                payload={"version_id": str(version.id)},
            ),
        )
        return signed_url, asset, version

    def read_file_bytes(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> Tuple[bytes, str, str]:
        signed_url, asset, version = self.get_download_access(file_id, organization_id, user_id)
        content = self.storage.read_bytes(version.bucket_reference, version.object_key)
        return content, version.detected_MIME_type, version.sanitized_filename
