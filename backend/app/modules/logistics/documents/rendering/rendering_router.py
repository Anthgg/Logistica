"""FastAPI router for Document Template and Rendering endpoints (Phase 014)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.rendering.rendering_service import DocumentRenderingService
from app.modules.logistics.documents.rendering.template_schemas import (
    DocumentPreviewRenderRequest,
    DocumentRendererStatusResponse,
    DocumentTemplateResponse,
    DocumentTemplateVersionResponse,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/document-templates", tags=["Logistics - Document Templates"])


@router.get(
    "",
    response_model=list[DocumentTemplateResponse],
    summary="Listar plantillas documentales disponibles",
)
def list_document_templates(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentTemplateResponse]:
    service = DocumentRenderingService(db)
    return service.list_templates()


@router.get(
    "/{template_key}",
    response_model=DocumentTemplateResponse,
    summary="Obtener detalle de plantilla por clave",
)
def get_document_template(
    template_key: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTemplateResponse:
    service = DocumentRenderingService(db)
    return service.get_template(template_key)


@router.get(
    "/{template_key}/versions",
    response_model=list[DocumentTemplateVersionResponse],
    summary="Listar versiones de una plantilla",
)
def list_template_versions(
    template_key: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentTemplateVersionResponse]:
    service = DocumentRenderingService(db)
    return service.list_versions(template_key)


@router.post(
    "/{template_key}/preview",
    response_class=Response,
    summary="Generar vista previa PDF de una plantilla documental",
    responses=PDF_RESPONSE_SCHEMA,
)
def render_template_preview_pdf(
    template_key: str,
    req: DocumentPreviewRenderRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = DocumentRenderingService(db)
    pdf_res = service.render_preview_pdf(template_key, req, user_id=str(principal.user_id))

    response = build_pdf_preview_response(
        pdf_res.pdf_bytes,
        pdf_res.filename_suggestion,
        extra_headers={
            "X-Document-Renderer": pdf_res.renderer_name,
            "X-Content-Hash": pdf_res.content_hash,
        },
    )

    AuditService().record(
        database=db,
        event_type="logistics.document_template.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_template",
        resource_id=template_key,
        event_metadata={
            "size_bytes": pdf_res.size_bytes,
            "renderer_name": pdf_res.renderer_name,
            "file_hash": pdf_res.file_hash,
        },
    )

    return response


@router.post(
    "/{template_key}/pdf",
    response_class=Response,
    summary="Descargar vista previa PDF de una plantilla documental",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_template_preview_pdf(
    template_key: str,
    req: DocumentPreviewRenderRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Same template render as the preview, delivered as an explicit download."""
    service = DocumentRenderingService(db)
    pdf_res = service.render_preview_pdf(template_key, req, user_id=str(principal.user_id))

    response = build_pdf_download_response(
        pdf_res.pdf_bytes,
        pdf_res.filename_suggestion,
        extra_headers={
            "X-Document-Renderer": pdf_res.renderer_name,
            "X-Content-Hash": pdf_res.content_hash,
        },
    )

    AuditService().record(
        database=db,
        event_type="logistics.document_template.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_template",
        resource_id=template_key,
        event_metadata={
            "size_bytes": pdf_res.size_bytes,
            "renderer_name": pdf_res.renderer_name,
            "file_hash": pdf_res.file_hash,
        },
    )

    return response


# Status Router under /api/logistics/document-renderer
status_router = APIRouter(prefix="/document-renderer", tags=["Logistics - Document Renderer"])


@status_router.get(
    "/status",
    response_model=DocumentRendererStatusResponse,
    summary="Obtener estado del motor de renderizado documental",
)
def get_document_renderer_status(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentRendererStatusResponse:
    service = DocumentRenderingService(db)
    return service.get_status()
