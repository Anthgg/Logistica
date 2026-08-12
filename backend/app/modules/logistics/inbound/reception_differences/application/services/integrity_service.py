from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...domain.services import canonical_hash_diff
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceCaseRevisionModel,
)


class ReceptionDifferenceIntegrityService:
    def __init__(self, db: Session):
        self.db = db

    def verify(self, case_id: UUID, organization_id: UUID) -> dict:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        revision = self.db.get(ReceptionDifferenceCaseRevisionModel, case.active_revision_id) if case.active_revision_id else None
        if not revision:
            return {"case_id": str(case_id), "status": "NO_REVISION", "message": "No hay revisión activa."}

        if revision.completion_snapshot:
            calculated_hash = canonical_hash_diff(revision.completion_snapshot)
        else:
            calculated_hash = revision.content_hash

        stored_hash = case.content_hash
        status = "VALID" if not stored_hash or stored_hash == calculated_hash else "MISMATCH"

        return {
            "case_id": str(case_id),
            "revision_id": str(revision.id),
            "revision_number": revision.revision_number,
            "status": status,
            "calculated_hash": calculated_hash,
            "stored_hash": stored_hash,
        }
