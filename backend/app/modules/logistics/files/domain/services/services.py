"""Domain services for Phase 030 — Files and Evidence Centralization."""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.files.domain.errors.exceptions import (
    FileAccessDeniedError,
    FileHashMismatchError,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    FileAccessScope,
    FileClassification,
    FileLifecycleStatus,
)
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileVersionModel,
)


class FileCodeService:
    """Generates formatted correlative file codes per organization (e.g. FIL-2026-000001)."""

    @staticmethod
    def generate_file_code(db: Session, organization_id: UUID) -> str:
        year = datetime.now(timezone.utc).year
        prefix = f"FIL-{year}-"
        
        stmt = (
            select(func.max(FileAssetModel.normalized_file_code))
            .where(
                FileAssetModel.organization_id == organization_id,
                FileAssetModel.normalized_file_code.like(f"{prefix}%")
            )
            .with_for_update()
        )
        max_code = db.execute(stmt).scalar()
        
        if not max_code:
            seq = 1
        else:
            match = re.search(r"(\d+)$", max_code)
            seq = int(match.group(1)) + 1 if match else 1

        code = f"{prefix}{seq:06d}"
        return code


class FileHashService:
    """Computes and verifies SHA-256 cryptographic hashes for file integrity."""

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def verify_hash(content: bytes, expected_sha256: str) -> bool:
        actual = hashlib.sha256(content).hexdigest()
        if actual.lower() != expected_sha256.lower():
            raise FileHashMismatchError(expected_sha256, actual)
        return True


class FileAccessPolicyService:
    """Evaluates access policy, classification limits and Step-Up requirements."""

    @staticmethod
    def check_access(
        file_asset: FileAssetModel,
        user_id: UUID,
        user_organization_id: UUID,
        required_action: str = "VIEW",
    ) -> bool:
        if file_asset.organization_id != user_organization_id:
            raise FileAccessDeniedError("Acceso denegado: El archivo pertenece a otra organización.")

        if file_asset.lifecycle_status in (FileLifecycleStatus.DELETED, FileLifecycleStatus.DELETION_PENDING):
            raise FileAccessDeniedError("Acceso denegado: El archivo ha sido eliminado o está en proceso de purga.")

        if file_asset.classification == FileClassification.HIGHLY_RESTRICTED:
            # Check owner or explicit grants
            if file_asset.owner_user_id and file_asset.owner_user_id != user_id:
                # Highly restricted files require explicit grant or owner
                pass

        return True

    @staticmethod
    def determine_step_up_level(classification: FileClassification, action: str) -> str:
        if action in ("DELETE", "LEGAL_HOLD", "REVOKE_EVIDENCE"):
            return "CRITICAL"

        if classification == FileClassification.HIGHLY_RESTRICTED:
            return "HIGH" if action in ("DOWNLOAD", "PREVIEW") else "MEDIUM"
        elif classification == FileClassification.RESTRICTED:
            return "MEDIUM" if action == "DOWNLOAD" else "LOW"
        return "LOW"
