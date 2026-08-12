"""FileAssociation application service for Phase 030."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.domain.errors.exceptions import (
    FileAssociationInvalidError,
    FileNotFoundError,
)
from app.modules.logistics.files.domain.value_objects.enums import ResourceType
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileAssociationModel,
)


class FileAssociationService:
    """Manages linkages between FileAssets and domain resources."""

    def __init__(self, db: Session):
        self.db = db

    def associate_file(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        resource_type: str,
        resource_id: str,
        association_type: str = "ATTACHMENT",
        is_primary: bool = False,
        file_version_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> FileAssociationModel:
        # Validate resource type
        valid_types = {rt.value for rt in ResourceType}
        if resource_type.upper() not in valid_types:
            raise FileAssociationInvalidError(resource_type, resource_id)

        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))

        assoc = FileAssociationModel(
            id=uuid4(),
            organization_id=organization_id,
            file_asset_id=file_id,
            file_version_id=file_version_id or asset.current_version_id,
            resource_type=resource_type.upper(),
            resource_id=str(resource_id),
            association_type=association_type.upper(),
            is_primary=is_primary,
            status="ACTIVE",
            created_by=user_id,
        )
        self.db.add(assoc)
        self.db.commit()
        self.db.refresh(assoc)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.associated",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_association",
                resource_id=str(assoc.id),
                correlation_id=correlation_id or str(assoc.id),
                payload={
                    "file_id": str(file_id),
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                },
            ),
        )
        return assoc

    def list_resource_files(
        self,
        organization_id: UUID,
        resource_type: str,
        resource_id: str,
    ) -> List[FileAssociationModel]:
        stmt = (
            select(FileAssociationModel)
            .where(
                FileAssociationModel.organization_id == organization_id,
                FileAssociationModel.resource_type == resource_type.upper(),
                FileAssociationModel.resource_id == str(resource_id),
                FileAssociationModel.status == "ACTIVE",
            )
            .order_by(FileAssociationModel.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def remove_association(
        self,
        association_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        assoc = self.db.execute(
            select(FileAssociationModel).where(
                FileAssociationModel.id == association_id,
                FileAssociationModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not assoc:
            return False

        assoc.status = "REMOVED"
        assoc.removed_by = user_id
        assoc.removed_at = datetime.now(timezone.utc)
        assoc.removal_reason = reason

        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.association_removed",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_association",
                resource_id=str(association_id),
                correlation_id=correlation_id or str(association_id),
                payload={"reason": reason},
            ),
        )
        return True
