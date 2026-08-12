"""FastAPI router for Document Catalog endpoints (Phase 011)."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.schemas import (
    DocumentCatalogValidationResponse,
    DocumentCatalogVersionResponse,
    DocumentFamilyListResponse,
    DocumentFamilyResponse,
    DocumentRetentionPolicyResponse,
    DocumentTypeDetailResponse,
    DocumentTypeListResponse,
    DocumentTypeSummaryResponse,
    DocumentTypeVersionResponse,
)
from app.modules.logistics.documents.service import DocumentCatalogService
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/document-catalog", tags=["Logistics - Document Catalog"])


@router.get(
    "",
    response_model=DocumentCatalogVersionResponse,
    summary="Obtener versión activa del catálogo documental",
)
def get_document_catalog_summary(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCatalogVersionResponse:
    service = DocumentCatalogService(db)
    return service.get_catalog_version()


@router.get(
    "/version",
    response_model=DocumentCatalogVersionResponse,
    summary="Obtener metadatos de versión del catálogo",
)
def get_document_catalog_version(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCatalogVersionResponse:
    service = DocumentCatalogService(db)
    return service.get_catalog_version()


@router.get(
    "/families",
    response_model=DocumentFamilyListResponse,
    summary="Listar familias documentales logísticas",
)
def list_document_families(
    status_filter: str | None = Query(None, alias="status"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentFamilyListResponse:
    service = DocumentCatalogService(db)
    items = service.list_families(status=status_filter)
    return DocumentFamilyListResponse(items=items, total=len(items))


@router.get(
    "/families/{family_code}",
    response_model=DocumentFamilyResponse,
    summary="Obtener detalle de una familia documental",
)
def get_document_family_detail(
    family_code: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentFamilyResponse:
    service = DocumentCatalogService(db)
    family = service.get_family_by_code(family_code.upper())
    if not family:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Familia '{family_code}' no encontrada.")
    return family


@router.get(
    "/retention-policies",
    response_model=list[DocumentRetentionPolicyResponse],
    summary="Listar políticas de retención documental",
)
def list_document_retention_policies(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentRetentionPolicyResponse]:
    service = DocumentCatalogService(db)
    return service.list_retention_policies()


@router.get(
    "/types",
    response_model=DocumentTypeListResponse,
    summary="Listar tipos documentales del catálogo",
)
def list_document_types(
    family_code: str | None = Query(None, alias="family"),
    origin_type: str | None = Query(None),
    owner_module: str | None = Query(None),
    catalog_status: str | None = Query(None, alias="status"),
    is_sensitive: bool | None = Query(None),
    search: str | None = Query(None),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTypeListResponse:
    service = DocumentCatalogService(db)
    items = service.list_document_types(
        family_code=family_code.upper() if family_code else None,
        origin_type=origin_type,
        owner_module=owner_module,
        catalog_status=catalog_status,
        is_sensitive=is_sensitive,
        search=search,
    )
    return DocumentTypeListResponse(items=items, total=len(items))


@router.get(
    "/types/{document_type_code}",
    response_model=DocumentTypeDetailResponse,
    summary="Obtener detalle completo de un tipo documental",
)
def get_document_type_detail(
    document_type_code: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTypeDetailResponse:
    service = DocumentCatalogService(db)
    dtype = service.get_document_type_detail(document_type_code.upper())
    if not dtype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo documental '{document_type_code}' no encontrado en el catálogo.",
        )
    return dtype


@router.get(
    "/types/{document_type_code}/versions",
    response_model=list[DocumentTypeVersionResponse],
    summary="Listar historial de versiones de un tipo documental",
)
def list_document_type_versions(
    document_type_code: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentTypeVersionResponse]:
    service = DocumentCatalogService(db)
    return service.list_type_versions(document_type_code.upper())


@router.get(
    "/types/{document_type_code}/active-version",
    response_model=DocumentTypeVersionResponse,
    summary="Obtener versión activa del contrato de un tipo documental",
)
def get_active_document_type_version(
    document_type_code: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTypeVersionResponse:
    service = DocumentCatalogService(db)
    active_ver = service.get_active_type_version(document_type_code.upper())
    if not active_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Versión activa no encontrada para el tipo '{document_type_code}'.",
        )
    return active_ver


@router.post(
    "/validate",
    response_model=DocumentCatalogValidationResponse,
    summary="Validar contrato del catálogo (Operación Administrativa Dry-Run)",
)
def validate_document_catalog(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.integrations.configure")),
    db: Session = Depends(get_db),
) -> DocumentCatalogValidationResponse:
    service = DocumentCatalogService(db)
    report = service.validate_catalog()

    AuditService().record(
        db=db,
        event_type="logistics.document_catalog.validated",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_catalog",
        resource_id=report.get("version"),
        event_metadata=report,
    )
    db.commit()
    return DocumentCatalogValidationResponse(**report)
