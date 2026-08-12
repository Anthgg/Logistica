"""Repository classes for Document Code Standard entities (Phase 012)."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.documents.codes.code_models import (
    DocumentCodeStandardModel,
    DocumentSiteCodeModel,
    DocumentTypeCodePolicyModel,
)


class DocumentCodeStandardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self) -> DocumentCodeStandardModel | None:
        return self.db.scalars(
            select(DocumentCodeStandardModel)
            .where(DocumentCodeStandardModel.status == "ACTIVE")
            .order_by(DocumentCodeStandardModel.created_at.desc())
        ).first()

    def get_by_version(self, version: str) -> DocumentCodeStandardModel | None:
        return self.db.scalars(
            select(DocumentCodeStandardModel).where(DocumentCodeStandardModel.version == version)
        ).first()

    def save(self, std: DocumentCodeStandardModel) -> DocumentCodeStandardModel:
        self.db.add(std)
        self.db.flush()
        return std


class DocumentSiteCodeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_primary_by_branch(self, branch_id: UUID) -> DocumentSiteCodeModel | None:
        return self.db.scalars(
            select(DocumentSiteCodeModel).where(
                DocumentSiteCodeModel.branch_id == branch_id,
                DocumentSiteCodeModel.is_primary.is_(True),
                DocumentSiteCodeModel.status == "ACTIVE",
            )
        ).first()

    def get_by_code(self, organization_id: UUID, code: str) -> DocumentSiteCodeModel | None:
        return self.db.scalars(
            select(DocumentSiteCodeModel).where(
                DocumentSiteCodeModel.organization_id == organization_id,
                DocumentSiteCodeModel.code == code.upper(),
            )
        ).first()

    def list_by_organization(self, organization_id: UUID) -> Sequence[DocumentSiteCodeModel]:
        return self.db.scalars(
            select(DocumentSiteCodeModel)
            .where(DocumentSiteCodeModel.organization_id == organization_id)
            .order_by(DocumentSiteCodeModel.code)
        ).all()

    def save(self, site_code: DocumentSiteCodeModel) -> DocumentSiteCodeModel:
        self.db.add(site_code)
        self.db.flush()
        return site_code


class DocumentTypeCodePolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_document_type(self, document_type_id: UUID) -> DocumentTypeCodePolicyModel | None:
        return self.db.scalars(
            select(DocumentTypeCodePolicyModel).where(
                DocumentTypeCodePolicyModel.document_type_id == document_type_id
            )
        ).first()

    def save(self, policy: DocumentTypeCodePolicyModel) -> DocumentTypeCodePolicyModel:
        self.db.add(policy)
        self.db.flush()
        return policy
