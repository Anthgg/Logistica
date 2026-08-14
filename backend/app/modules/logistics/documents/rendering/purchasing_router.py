"""FastAPI router for Purchasing Document Preview and PDF endpoints (Phase 015)."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.rendering.filenames import preview_pdf_filename
from app.modules.logistics.documents.rendering.purchasing_service import PurchasingRenderingService
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/purchasing/documents", tags=["Logistics - Purchasing Documents"])


@router.post(
    "/{document_type_code}/preview",
    response_class=Response,
    summary="Generar vista previa PDF de documento de compras (REQ, SCOT, CCO, OC, APC, CEP)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_purchasing_document(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = PurchasingRenderingService(db)
    pdf_res = service.render_purchasing_preview(document_type_code, payload, user_id=str(principal.user_id))

    response = build_pdf_preview_response(
        pdf_res.pdf_bytes,
        pdf_res.filename_suggestion,
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Content-Hash": pdf_res.content_hash,
        },
    )

    AuditService().record(
        database=db,
        event_type="logistics.purchasing_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="purchasing_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "renderer_name": pdf_res.renderer_name,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
        },
    )

    return response


@router.post(
    "/{document_type_code}/pdf",
    response_class=Response,
    summary="Descargar archivo PDF renderizado de compras (Modo Preview Protegido)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_purchasing_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = PurchasingRenderingService(db)
    pdf_res = service.render_purchasing_preview(document_type_code, payload, user_id=str(principal.user_id))

    response = build_pdf_download_response(
        pdf_res.pdf_bytes,
        preview_pdf_filename(document_type_code),
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
        },
    )

    AuditService().record(
        database=db,
        event_type="logistics.purchasing_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="purchasing_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
        },
    )

    return response
