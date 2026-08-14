"""FastAPI router for Inbound & Quality Document Preview, PDF, and Package Manifest endpoints (Phase 016)."""

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
from app.modules.logistics.documents.rendering.inbound_schemas import ReceptionPackageManifestResponse
from app.modules.logistics.documents.rendering.inbound_service import InboundRenderingService
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/inbound", tags=["Logistics - Inbound Documents"])


@router.post(
    "/documents/{document_type_code}/preview",
    response_class=Response,
    summary="Generar vista previa PDF de documento de recepción (CIT, CPV, AREC, NI, DIF, NC)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_inbound_document(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = InboundRenderingService(db)
    pdf_res = service.render_inbound_preview(document_type_code, payload, user_id=str(principal.user_id))

    AuditService().record(
        db=db,
        event_type="logistics.inbound_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="inbound_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "renderer_name": pdf_res.renderer_name,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
        },
    )
    db.commit()

    return build_pdf_preview_response(
        pdf_res.pdf_bytes,
        pdf_res.filename_suggestion,
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Content-Hash": pdf_res.content_hash,
        },
    )


@router.post(
    "/documents/{document_type_code}/pdf",
    response_class=Response,
    summary="Descargar archivo PDF renderizado de recepción (Modo Preview Protegido)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_inbound_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = InboundRenderingService(db)
    pdf_res = service.render_inbound_preview(document_type_code, payload, user_id=str(principal.user_id))

    AuditService().record(
        db=db,
        event_type="logistics.inbound_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="inbound_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
        },
    )
    db.commit()

    return build_pdf_download_response(
        pdf_res.pdf_bytes,
        preview_pdf_filename(document_type_code),
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
        },
    )


@router.post(
    "/document-package/manifest",
    response_model=ReceptionPackageManifestResponse,
    summary="Evaluar y obtener el manifiesto del paquete documental de recepción",
)
def get_reception_package_manifest(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> ReceptionPackageManifestResponse:
    service = InboundRenderingService(db)
    manifest = service.build_reception_package_manifest(payload)

    AuditService().record(
        db=db,
        event_type="logistics.inbound_document.package_manifest_created",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="reception_package_manifest",
        resource_id="MANIFEST_PREVIEW",
        event_metadata={
            "included_count": len(manifest.included_documents),
            "missing_count": len(manifest.missing_documents),
        },
    )
    db.commit()

    return manifest
