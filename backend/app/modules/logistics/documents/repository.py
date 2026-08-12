"""Repository classes for Document Catalog entities (Phase 011)."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.logistics.documents.models import (
    DocumentCatalogVersionModel,
    DocumentFamilyModel,
    DocumentRetentionPolicyModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
)


class DocumentFamilyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> DocumentFamilyModel | None:
        return self.db.scalars(
            select(DocumentFamilyModel).where(DocumentFamilyModel.code == code)
        ).first()

    def list_all(self, status: str | None = None) -> Sequence[DocumentFamilyModel]:
        stmt = select(DocumentFamilyModel).order_by(DocumentFamilyModel.display_order)
        if status:
            stmt = stmt.where(DocumentFamilyModel.status == status)
        return self.db.scalars(stmt).all()

    def save(self, family: DocumentFamilyModel) -> DocumentFamilyModel:
        self.db.add(family)
        self.db.flush()
        return family


class DocumentRetentionPolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> DocumentRetentionPolicyModel | None:
        return self.db.scalars(
            select(DocumentRetentionPolicyModel).where(DocumentRetentionPolicyModel.code == code)
        ).first()

    def list_all(self) -> Sequence[DocumentRetentionPolicyModel]:
        return self.db.scalars(select(DocumentRetentionPolicyModel)).all()

    def save(self, policy: DocumentRetentionPolicyModel) -> DocumentRetentionPolicyModel:
        self.db.add(policy)
        self.db.flush()
        return policy


class DocumentTypeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> DocumentTypeModel | None:
        return self.db.scalars(
            select(DocumentTypeModel)
            .options(joinedload(DocumentTypeModel.family), joinedload(DocumentTypeModel.versions))
            .where(DocumentTypeModel.code == code)
        ).first()

    def list(
        self,
        family_code: str | None = None,
        origin_type: str | None = None,
        owner_module: str | None = None,
        catalog_status: str | None = None,
        is_sensitive: bool | None = None,
        search: str | None = None,
    ) -> Sequence[DocumentTypeModel]:
        stmt = (
            select(DocumentTypeModel)
            .options(joinedload(DocumentTypeModel.family))
            .order_by(DocumentTypeModel.display_order)
        )
        if family_code:
            stmt = stmt.join(DocumentTypeModel.family).where(DocumentFamilyModel.code == family_code)
        if origin_type:
            stmt = stmt.where(DocumentTypeModel.origin_type == origin_type)
        if owner_module:
            stmt = stmt.where(DocumentTypeModel.owner_module == owner_module)
        if catalog_status:
            stmt = stmt.where(DocumentTypeModel.catalog_status == catalog_status)
        if is_sensitive is not None:
            stmt = stmt.where(DocumentTypeModel.is_sensitive == is_sensitive)
        if search:
            stmt = stmt.where(
                (DocumentTypeModel.code.ilike(f"%{search}%"))
                | (DocumentTypeModel.name.ilike(f"%{search}%"))
            )
        return self.db.scalars(stmt).unique().all()

    def save(self, doc_type: DocumentTypeModel) -> DocumentTypeModel:
        self.db.add(doc_type)
        self.db.flush()
        return doc_type


class DocumentTypeVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_type_and_version(
        self, document_type_id: UUID, version: str
    ) -> DocumentTypeVersionModel | None:
        return self.db.scalars(
            select(DocumentTypeVersionModel).where(
                DocumentTypeVersionModel.document_type_id == document_type_id,
                DocumentTypeVersionModel.version == version,
            )
        ).first()

    def get_active_version(self, document_type_id: UUID) -> DocumentTypeVersionModel | None:
        return self.db.scalars(
            select(DocumentTypeVersionModel).where(
                DocumentTypeVersionModel.document_type_id == document_type_id,
                DocumentTypeVersionModel.status == "ACTIVE",
            )
        ).first()

    def list_versions_by_type(self, document_type_id: UUID) -> Sequence[DocumentTypeVersionModel]:
        return self.db.scalars(
            select(DocumentTypeVersionModel)
            .where(DocumentTypeVersionModel.document_type_id == document_type_id)
            .order_by(DocumentTypeVersionModel.created_at.desc())
        ).all()

    def save(self, version_model: DocumentTypeVersionModel) -> DocumentTypeVersionModel:
        self.db.add(version_model)
        self.db.flush()
        return version_model


class DocumentCatalogVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_current_active(self) -> DocumentCatalogVersionModel | None:
        return self.db.scalars(
            select(DocumentCatalogVersionModel)
            .where(DocumentCatalogVersionModel.status == "ACTIVE")
            .order_by(DocumentCatalogVersionModel.released_at.desc())
        ).first()

    def save(self, catalog_ver: DocumentCatalogVersionModel) -> DocumentCatalogVersionModel:
        self.db.add(catalog_ver)
        self.db.flush()
        return catalog_ver
