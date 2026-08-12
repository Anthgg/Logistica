"""Evidence and Chain of Custody application service for Phase 030."""

import hashlib

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.domain.errors.exceptions import (
    EvidenceAlreadyAcceptedError,
    EvidenceImmutableError,
    EvidenceNotFoundError,
    FileNotFoundError,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    EvidenceAcceptanceStatus,
    EvidenceStatus,
)
from app.modules.logistics.files.infrastructure.persistence.models import (
    EvidenceCustodyEventModel,
    EvidenceRecordModel,
    FileAssetModel,
    FileVersionModel,
)


class EvidenceCustodyService:
    """Manages immutable EvidenceRecords and append-only Chain of Custody logs."""

    def __init__(self, db: Session):
        self.db = db

    def register_evidence(
        self,
        organization_id: UUID,
        user_id: UUID,
        file_asset_id: UUID,
        evidence_type: str,
        subject_type: str,
        subject_id: str,
        description: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EvidenceRecordModel:
        asset = self.db.execute(
            select(FileAssetModel).where(
                FileAssetModel.id == file_asset_id,
                FileAssetModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not asset:
            raise FileNotFoundError(str(file_asset_id))

        version_id = asset.current_version_id
        ev_id = uuid4()
        code = f"EVD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{ev_id.hex[:6].upper()}"

        evidence = EvidenceRecordModel(
            id=ev_id,
            organization_id=organization_id,
            evidence_code=code,
            evidence_type=evidence_type.upper(),
            subject_type=subject_type.upper(),
            subject_id=str(subject_id),
            file_asset_id=file_asset_id,
            file_version_id=version_id,
            captured_by_user_id=user_id,
            description=description,
            status=EvidenceStatus.CANDIDATE.value,
            acceptance_status=EvidenceAcceptanceStatus.PENDING.value,
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        # Log Custody Event CAPTURED
        self._record_custody_event(
            evidence_id=ev_id,
            organization_id=organization_id,
            file_version_id=version_id,
            event_type="CAPTURED",
            user_id=user_id,
            correlation_id=correlation_id or str(ev_id),
            reason="Captura inicial de evidencia en plataforma.",
        )

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.evidence.created",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="evidence_record",
                resource_id=str(ev_id),
                correlation_id=correlation_id or str(ev_id),
                payload={"evidence_code": code, "evidence_type": evidence_type},
            ),
        )
        return evidence

    def accept_evidence(
        self,
        evidence_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        correlation_id: Optional[str] = None,
    ) -> EvidenceRecordModel:
        evidence = self.db.execute(
            select(EvidenceRecordModel).where(
                EvidenceRecordModel.id == evidence_id,
                EvidenceRecordModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not evidence:
            raise EvidenceNotFoundError(str(evidence_id))

        if evidence.acceptance_status == EvidenceAcceptanceStatus.ACCEPTED.value:
            raise EvidenceAlreadyAcceptedError(str(evidence_id))

        evidence.acceptance_status = EvidenceAcceptanceStatus.ACCEPTED.value
        evidence.status = EvidenceStatus.ACCEPTED.value
        evidence.accepted_by = user_id
        evidence.accepted_at = datetime.now(timezone.utc)

        # Update Asset evidence status
        asset = self.db.execute(
            select(FileAssetModel).where(FileAssetModel.id == evidence.file_asset_id)
        ).scalar_one_or_none()
        if asset:
            asset.evidence_status = EvidenceStatus.ACCEPTED.value

        self.db.commit()
        self.db.refresh(evidence)

        self._record_custody_event(
            evidence_id=evidence_id,
            organization_id=organization_id,
            file_version_id=evidence.file_version_id,
            event_type="ACCEPTED",
            user_id=user_id,
            correlation_id=correlation_id or str(evidence_id),
            reason="Aceptación formal e inmutable de la evidencia.",
        )

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.evidence.accepted",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="evidence_record",
                resource_id=str(evidence_id),
                correlation_id=correlation_id or str(evidence_id),
            ),
        )
        return evidence

    def revoke_evidence(
        self,
        evidence_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
        correlation_id: Optional[str] = None,
    ) -> EvidenceRecordModel:
        evidence = self.db.execute(
            select(EvidenceRecordModel).where(
                EvidenceRecordModel.id == evidence_id,
                EvidenceRecordModel.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not evidence:
            raise EvidenceNotFoundError(str(evidence_id))

        evidence.acceptance_status = EvidenceAcceptanceStatus.REVOKED.value
        evidence.status = EvidenceStatus.REVOKED.value
        evidence.revoked_by = user_id
        evidence.revoked_at = datetime.now(timezone.utc)
        evidence.revocation_reason = reason

        self.db.commit()
        self.db.refresh(evidence)

        self._record_custody_event(
            evidence_id=evidence_id,
            organization_id=organization_id,
            file_version_id=evidence.file_version_id,
            event_type="REVOKED",
            user_id=user_id,
            correlation_id=correlation_id or str(evidence_id),
            reason=reason,
        )

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.evidence.revoked",
                actor_user_id=user_id,
                organization_id=organization_id,
                resource_type="evidence_record",
                resource_id=str(evidence_id),
                correlation_id=correlation_id or str(evidence_id),
                payload={"reason": reason},
            ),
        )
        return evidence

    def get_custody_events(
        self, evidence_id: UUID, organization_id: UUID
    ) -> List[EvidenceCustodyEventModel]:
        stmt = (
            select(EvidenceCustodyEventModel)
            .where(
                EvidenceCustodyEventModel.evidence_id == evidence_id,
                EvidenceCustodyEventModel.organization_id == organization_id,
            )
            .order_by(EvidenceCustodyEventModel.event_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_evidence(
        self,
        organization_id: UUID,
        evidence_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: Optional[str] = None,
        acceptance_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[EvidenceRecordModel], int]:
        from sqlalchemy import func

        stmt = select(EvidenceRecordModel).where(EvidenceRecordModel.organization_id == organization_id)
        if evidence_type:
            stmt = stmt.where(EvidenceRecordModel.evidence_type == evidence_type.upper())
        if subject_type:
            stmt = stmt.where(EvidenceRecordModel.subject_type == subject_type.upper())
        if subject_id:
            stmt = stmt.where(EvidenceRecordModel.subject_id == subject_id)
        if status:
            stmt = stmt.where(EvidenceRecordModel.status == status.upper())
        if acceptance_status:
            stmt = stmt.where(EvidenceRecordModel.acceptance_status == acceptance_status.upper())

        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(EvidenceRecordModel.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def _record_custody_event(
        self,
        evidence_id: UUID,
        organization_id: UUID,
        file_version_id: UUID,
        event_type: str,
        user_id: UUID,
        correlation_id: str,
        reason: Optional[str] = None,
    ):
        event_at = datetime.now(timezone.utc)
        payload = f"{evidence_id}:{event_type}:{event_at.isoformat()}:{user_id}"
        event_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        custody_event = EvidenceCustodyEventModel(
            id=uuid4(),
            organization_id=organization_id,
            evidence_id=evidence_id,
            file_version_id=file_version_id,
            event_type=event_type,
            actor_type="USER",
            actor_user_id=user_id,
            event_at=event_at,
            reason=reason,
            event_hash=event_hash,
            correlation_id=correlation_id,
        )
        self.db.add(custody_event)
        self.db.commit()

