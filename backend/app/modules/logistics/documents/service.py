"""Application service for Document Catalog (Phase 011)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.documents.catalog.loader import load_catalog_json
from app.modules.logistics.documents.catalog.validator import validate_catalog_data
from app.modules.logistics.documents.models import DocumentTypeModel, DocumentTypeVersionModel
from app.modules.logistics.documents.repository import (
    DocumentCatalogVersionRepository,
    DocumentFamilyRepository,
    DocumentRetentionPolicyRepository,
    DocumentTypeRepository,
    DocumentTypeVersionRepository,
)
from app.modules.logistics.documents.schemas import (
    DocumentCatalogVersionResponse,
    DocumentFamilyResponse,
    DocumentRetentionPolicyResponse,
    DocumentTypeDetailResponse,
    DocumentTypeSummaryResponse,
    DocumentTypeVersionResponse,
)


class DocumentCatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.fam_repo = DocumentFamilyRepository(db)
        self.ret_repo = DocumentRetentionPolicyRepository(db)
        self.type_repo = DocumentTypeRepository(db)
        self.ver_repo = DocumentTypeVersionRepository(db)
        self.cat_ver_repo = DocumentCatalogVersionRepository(db)

    def get_catalog_version(self) -> DocumentCatalogVersionResponse:
        cat_ver = self.cat_ver_repo.get_current_active()
        data = load_catalog_json()
        return DocumentCatalogVersionResponse(
            version=cat_ver.version if cat_ver else data.get("catalog_version", "1.0.0"),
            status=cat_ver.status if cat_ver else "ACTIVE",
            released_at=cat_ver.released_at if cat_ver else data.get("released_at", "2026-07-26T00:00:00Z"),
            checksum=cat_ver.checksum if cat_ver else "v1.0.0-checksum",
            total_families=len(data.get("families", [])),
            total_document_types=len(data.get("document_types", [])),
            total_proposed_types=len(data.get("proposed_types", [])),
        )

    def list_families(self, status: str | None = None) -> list[DocumentFamilyResponse]:
        families = self.fam_repo.list_all(status=status)
        return [DocumentFamilyResponse.model_validate(f) for f in families]

    def get_family_by_code(self, code: str) -> DocumentFamilyResponse | None:
        family = self.fam_repo.get_by_code(code)
        if not family:
            return None
        return DocumentFamilyResponse.model_validate(family)

    def list_retention_policies(self) -> list[DocumentRetentionPolicyResponse]:
        policies = self.ret_repo.list_all()
        return [DocumentRetentionPolicyResponse.model_validate(p) for p in policies]

    def list_document_types(
        self,
        family_code: str | None = None,
        origin_type: str | None = None,
        owner_module: str | None = None,
        catalog_status: str | None = None,
        is_sensitive: bool | None = None,
        search: str | None = None,
    ) -> list[DocumentTypeSummaryResponse]:
        types = self.type_repo.list(
            family_code=family_code,
            origin_type=origin_type,
            owner_module=owner_module,
            catalog_status=catalog_status,
            is_sensitive=is_sensitive,
            search=search,
        )
        items: list[DocumentTypeSummaryResponse] = []
        for t in types:
            items.append(
                DocumentTypeSummaryResponse(
                    id=t.id,
                    code=t.code,
                    name=t.name,
                    short_name=t.short_name,
                    description=t.description,
                    family_code=t.family.code if t.family else "",
                    family_name=t.family.name if t.family else "",
                    origin_type=t.origin_type,
                    owner_module=t.owner_module,
                    resource_type=t.resource_type,
                    catalog_status=t.catalog_status,
                    is_sensitive=t.is_sensitive,
                    supports_issue=t.supports_issue,
                    supports_reprint=t.supports_reprint,
                    supports_cancel=t.supports_cancel,
                    requires_qr=t.requires_qr,
                    requires_signature=t.requires_signature,
                    display_order=t.display_order,
                    created_at=t.created_at,
                )
            )
        return items

    def get_document_type_detail(self, code: str) -> DocumentTypeDetailResponse | None:
        t = self.type_repo.get_by_code(code)
        if not t:
            return None

        active_ver = self.ver_repo.get_active_version(t.id)
        active_ver_resp = (
            DocumentTypeVersionResponse.model_validate(active_ver) if active_ver else None
        )

        return DocumentTypeDetailResponse(
            id=t.id,
            code=t.code,
            name=t.name,
            short_name=t.short_name,
            description=t.description,
            family_code=t.family.code if t.family else "",
            family_name=t.family.name if t.family else "",
            origin_type=t.origin_type,
            owner_module=t.owner_module,
            resource_type=t.resource_type,
            catalog_status=t.catalog_status,
            is_sensitive=t.is_sensitive,
            supports_issue=t.supports_issue,
            supports_reprint=t.supports_reprint,
            supports_cancel=t.supports_cancel,
            requires_qr=t.requires_qr,
            requires_signature=t.requires_signature,
            display_order=t.display_order,
            created_at=t.created_at,
            active_version=active_ver_resp,
            is_system=t.is_system,
            is_official_external=t.is_official_external,
            supports_internal_number=t.supports_internal_number,
            supports_external_number=t.supports_external_number,
            supports_series=t.supports_series,
            supports_talonario=t.supports_talonario,
            supports_preview=t.supports_preview,
            supports_download=t.supports_download,
            supports_bulk_download=t.supports_bulk_download,
            supports_public_verification=t.supports_public_verification,
            requires_reason_on_reprint=t.requires_reason_on_reprint,
            requires_reason_on_cancel=t.requires_reason_on_cancel,
        )

    def list_type_versions(self, code: str) -> list[DocumentTypeVersionResponse]:
        t = self.type_repo.get_by_code(code)
        if not t:
            return []
        versions = self.ver_repo.list_versions_by_type(t.id)
        return [DocumentTypeVersionResponse.model_validate(v) for v in versions]

    def get_active_type_version(self, code: str) -> DocumentTypeVersionResponse | None:
        t = self.type_repo.get_by_code(code)
        if not t:
            return None
        active_ver = self.ver_repo.get_active_version(t.id)
        if not active_ver:
            return None
        return DocumentTypeVersionResponse.model_validate(active_ver)

    def validate_catalog(self) -> dict[str, Any]:
        data = load_catalog_json()
        return validate_catalog_data(data)
