"""FastAPI router for Document Code Standard endpoints (Phase 012)."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.codes.code_schemas import (
    DocumentCodeExamplesResponse,
    DocumentCodeParseResponse,
    DocumentCodePreviewRequest,
    DocumentCodePreviewResponse,
    DocumentCodeStandardResponse,
    DocumentCodeValidationRequest,
    DocumentCodeValidationResponse,
    DocumentSiteCodeResponse,
)
from app.modules.logistics.documents.codes.code_service import DocumentCodeStandardService
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/document-code-standard", tags=["Logistics - Document Code Standard"])


@router.get(
    "",
    response_model=DocumentCodeStandardResponse,
    summary="Obtener norma técnica activa de códigos documentales",
)
def get_active_document_code_standard(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCodeStandardResponse:
    service = DocumentCodeStandardService(db)
    return service.get_active_standard()


@router.get(
    "/versions",
    response_model=list[DocumentCodeStandardResponse],
    summary="Listar versiones del estándar de codificación",
)
def list_document_code_standard_versions(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentCodeStandardResponse]:
    service = DocumentCodeStandardService(db)
    active = service.get_active_standard()
    return [active]


@router.get(
    "/examples",
    response_model=DocumentCodeExamplesResponse,
    summary="Obtener ejemplos aprobados por tipo y familia documental",
)
def get_approved_document_code_examples(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCodeExamplesResponse:
    service = DocumentCodeStandardService(db)
    return service.get_approved_examples()


@router.post(
    "/validate",
    response_model=DocumentCodeValidationResponse,
    summary="Validar estructura y semántica de un código documental",
)
def validate_document_code(
    req: DocumentCodeValidationRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCodeValidationResponse:
    service = DocumentCodeStandardService(db)
    return service.validate_code(req.code)


@router.post(
    "/parse",
    response_model=DocumentCodeParseResponse,
    summary="Analizar y descomponer un código documental en sus 4 partes",
)
def parse_document_code(
    req: DocumentCodeValidationRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCodeParseResponse:
    service = DocumentCodeStandardService(db)
    try:
        return service.parse_code(req.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/preview",
    response_model=DocumentCodePreviewResponse,
    summary="Generar vista previa sin reserva de correlativo",
)
def preview_document_code(
    req: DocumentCodePreviewRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentCodePreviewResponse:
    service = DocumentCodeStandardService(db)
    preview = service.preview_code(req)

    AuditService().record(
        db=db,
        event_type="logistics.document_code.preview_generated",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_code_preview",
        resource_id=preview.code_preview,
        event_metadata={"preview": preview.model_dump()},
    )
    db.commit()
    return preview


# Site Codes Router under /api/logistics/document-site-codes
site_codes_router = APIRouter(prefix="/document-site-codes", tags=["Logistics - Document Site Codes"])


@site_codes_router.get(
    "",
    response_model=list[DocumentSiteCodeResponse],
    summary="Listar códigos documentales de sedes de la organización",
)
def list_document_site_codes(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentSiteCodeResponse]:
    service = DocumentCodeStandardService(db)
    return service.list_site_codes(principal.organization_id)
