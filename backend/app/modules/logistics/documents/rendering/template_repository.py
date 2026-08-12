"""Repository classes for Document Templates and Versions (Phase 014)."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.template_models import (
    DocumentTemplateAssetModel,
    DocumentTemplateModel,
    DocumentTemplateVersionModel,
)


class DocumentTemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_key(self, template_key: str) -> DocumentTemplateModel | None:
        return self.db.scalars(
            select(DocumentTemplateModel).where(DocumentTemplateModel.template_key == template_key)
        ).first()

    def list(self, status: str | None = None) -> Sequence[DocumentTemplateModel]:
        stmt = select(DocumentTemplateModel)
        if status:
            stmt = stmt.where(DocumentTemplateModel.status == status)
        return self.db.scalars(stmt.order_by(DocumentTemplateModel.template_key.asc())).all()

    def save(self, template: DocumentTemplateModel) -> DocumentTemplateModel:
        self.db.add(template)
        self.db.flush()
        return template


class DocumentTemplateVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self, template_id: UUID) -> DocumentTemplateVersionModel | None:
        return self.db.scalars(
            select(DocumentTemplateVersionModel).where(
                DocumentTemplateVersionModel.template_id == template_id,
                DocumentTemplateVersionModel.status == "ACTIVE",
            )
        ).first()

    def get_by_version(self, template_id: UUID, version: str) -> DocumentTemplateVersionModel | None:
        return self.db.scalars(
            select(DocumentTemplateVersionModel).where(
                DocumentTemplateVersionModel.template_id == template_id,
                DocumentTemplateVersionModel.version == version,
            )
        ).first()

    def list_versions(self, template_id: UUID) -> Sequence[DocumentTemplateVersionModel]:
        return self.db.scalars(
            select(DocumentTemplateVersionModel)
            .where(DocumentTemplateVersionModel.template_id == template_id)
            .order_by(DocumentTemplateVersionModel.created_at.desc())
        ).all()

    def save(self, ver: DocumentTemplateVersionModel) -> DocumentTemplateVersionModel:
        self.db.add(ver)
        self.db.flush()
        return ver
