"""Retention Policy, Legal Holds and Controlled Deletion application service for Phase 030."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.domain.errors.exceptions import (
    FileDeletionBlockedError,
    FileLegalHoldActiveError,
    FileNotFoundError,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    FileDeletionRequestStatus,
    FileLifecycleStatus,
    LegalHoldStatus,
)
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileDeletionRequestModel,
    FileLegalHoldModel,
    FileRetentionPolicyModel,
)


class RetentionLegalHoldService:
    """Manages document retention policies, active legal holds and controlled deletion approvals."""

    def __init__(self, db: Session):
        self.db = db

    def apply_legal_hold(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
        authority_reference: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> FileLegalHoldModel:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))

        hold = FileLegalHoldModel(
            id=uuid4(),
            file_asset_id=file_id,
            file_version_id=asset.current_version_id,
            reason=reason,
            authority_reference=authority_reference,
            applied_by=user_id,
            status=LegalHoldStatus.ACTIVE.value,
        )
        self.db.add(hold)
        self.db.commit()
        self.db.refresh(hold)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.legal_hold_applied",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_legal_hold",
                resource_id=str(hold.id),
                correlation_id=correlation_id or str(hold.id),
                payload={"reason": reason, "authority": authority_reference},
            ),
        )
        return hold

    def release_legal_hold(
        self,
        hold_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        release_reason: str,
        correlation_id: Optional[str] = None,
    ) -> FileLegalHoldModel:
        hold = self.db.execute(
            select(FileLegalHoldModel).where(FileLegalHoldModel.id == hold_id)
        ).scalar_one_or_none()
        if not hold:
            raise FileNotFoundError(str(hold_id))

        hold.status = LegalHoldStatus.RELEASED.value
        hold.released_by = user_id
        hold.released_at = datetime.now(timezone.utc)
        hold.release_reason = release_reason

        self.db.commit()
        self.db.refresh(hold)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.legal_hold_released",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_legal_hold",
                resource_id=str(hold_id),
                correlation_id=correlation_id or str(hold_id),
                payload={"reason": release_reason},
            ),
        )
        return hold

    def request_file_deletion(
        self,
        file_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
        deletion_basis: str = "USER_REQUEST",
        correlation_id: Optional[str] = None,
    ) -> FileDeletionRequestModel:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_id))

        # Verify active legal holds
        active_hold = self.db.execute(
            select(FileLegalHoldModel).where(
                FileLegalHoldModel.file_asset_id == file_id,
                FileLegalHoldModel.status == LegalHoldStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        if active_hold:
            raise FileLegalHoldActiveError(str(file_id))

        request = FileDeletionRequestModel(
            id=uuid4(),
            file_asset_id=file_id,
            requested_by=user_id,
            reason=reason,
            deletion_basis=deletion_basis,
            status=FileDeletionRequestStatus.REQUESTED.value,
        )
        self.db.add(request)

        asset.deletion_requested_at = datetime.now(timezone.utc)
        asset.deletion_requested_by = user_id

        self.db.commit()
        self.db.refresh(request)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.deletion_requested",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_deletion_request",
                resource_id=str(request.id),
                correlation_id=correlation_id or str(request.id),
                payload={"reason": reason},
            ),
        )
        return request

    def approve_file_deletion(
        self,
        request_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        correlation_id: Optional[str] = None,
    ) -> FileDeletionRequestModel:
        req = self.db.execute(
            select(FileDeletionRequestModel).where(FileDeletionRequestModel.id == request_id)
        ).scalar_one_or_none()
        if not req:
            raise FileNotFoundError(str(request_id))

        asset = self.db.execute(
            select(FileAssetModel).where(FileAssetModel.id == req.file_asset_id)
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(req.file_asset_id))

        req.status = FileDeletionRequestStatus.APPROVED.value
        req.reviewed_by = user_id
        req.reviewed_at = datetime.now(timezone.utc)

        # Soft delete logic (tombstone)
        asset.lifecycle_status = FileLifecycleStatus.DELETED.value

        self.db.commit()
        self.db.refresh(req)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.file.deletion_approved",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="file_deletion_request",
                resource_id=str(request_id),
                correlation_id=correlation_id or str(request_id),
            ),
        )
        return req
