"""FastAPI router for transport document rendering and manifests (Phase 019)."""

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
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.documents.rendering.transport_service import TransportRenderingService
from app.modules.logistics.documents.rendering.delivery_schemas import (
    TransportDeliveryDocumentPackageManifest,
)
from app.modules.logistics.documents.rendering.filenames import preview_pdf_filename
from app.services.audit_service import AuditService

router = APIRouter(prefix="/transport", tags=["Logistics Transport Documents"])

PACKAGE_PDF_FILENAME = "PREVIEW-PAQUETE-TRANSPORTE-COMBINADO.pdf"


@router.post(
    "/documents/{document_type_code}/preview",
    response_class=Response,
    summary="Previsualizar PDF de documento de transporte (Modo Preview Protegido)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_transport_document(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.transport_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    sensitive_read = principal.has_permission("logistics.transport_documents.read_sensitive")
    service = TransportRenderingService(db)
    
    pdf_res = service.render_transport_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        sensitive_read=sensitive_read,
    )

    response = build_pdf_preview_response(
        pdf_res.pdf_bytes,
        pdf_res.filename_suggestion,
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Content-Hash": pdf_res.content_hash,
            "X-Template-Version": "1.0.0",
        },
    )

    AuditService().record(
        db=db,
        event_type="logistics.transport_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="transport_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
            "sensitive_read": sensitive_read,
        },
    )
    db.commit()

    return response


@router.post(
    "/documents/{document_type_code}/pdf",
    response_class=Response,
    summary="Descargar PDF de documento de transporte (Modo Preview Protegido)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_transport_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.transport_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    sensitive_read = principal.has_permission("logistics.transport_documents.read_sensitive")
    service = TransportRenderingService(db)
    
    pdf_res = service.render_transport_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        sensitive_read=sensitive_read,
    )

    response = build_pdf_download_response(
        pdf_res.pdf_bytes,
        preview_pdf_filename(document_type_code),
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Template-Version": "1.0.0",
        },
    )

    AuditService().record(
        db=db,
        event_type="logistics.transport_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="transport_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
            "sensitive_read": sensitive_read,
        },
    )
    db.commit()

    return response


@router.post(
    "/document-package/manifest",
    response_model=TransportDeliveryDocumentPackageManifest,
    summary="Evaluar y obtener el manifiesto del paquete documental de transporte",
)
def get_transport_package_manifest(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.transport_documents.read")),
    db: Session = Depends(get_db),
) -> TransportDeliveryDocumentPackageManifest:
    service = TransportRenderingService(db)
    manifest = service.build_transport_delivery_package_manifest(payload)

    AuditService().record(
        db=db,
        event_type="logistics.transport_document.package_manifest_created",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="transport_package_manifest",
        resource_id="MANIFEST_PREVIEW",
        event_metadata={
            "package_mode": manifest.package_mode,
            "documents_count": len(manifest.document_entries),
            "warnings_count": len(manifest.warnings),
            "preview_mode": True,
        },
    )
    db.commit()

    return manifest


def _render_transport_package_pdf(
    payload: dict[str, Any],
    principal: LogisticsPrincipal,
    db: Session,
):
    """Render the combined transport package PDF.

    Shared by the preview and download endpoints so both always deliver exactly
    the same bytes. Rendering only: the caller records the preview or download
    event once the PDF has been validated, so a failed render is never audited
    as a successful one.
    """
    sensitive_read = principal.has_permission("logistics.transport_documents.read_sensitive")
    service = TransportRenderingService(db)
    manifest = service.build_transport_delivery_package_manifest(payload)

    target_code = "HV"
    for entry in manifest.document_entries:
        if entry.included:
            target_code = entry.document_type_code
            break

    doc_data = payload.get("document_data", {}).get(target_code, payload)
    pdf_res = service.render_transport_preview(
        document_type_code=target_code,
        data=doc_data,
        user_id=str(principal.user_id),
        sensitive_read=sensitive_read,
    )

    return pdf_res, manifest, target_code


def _record_transport_package_event(
    db: Session,
    principal: LogisticsPrincipal,
    manifest,
    pdf_res,
    target_code: str,
    *,
    downloaded: bool,
) -> None:
    """Record the package preview/download event. Call only after validation."""
    AuditService().record(
        db=db,
        event_type=(
            "logistics.transport_document.package_preview_downloaded"
            if downloaded
            else "logistics.transport_document.package_preview_rendered"
        ),
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="transport_package_preview",
        resource_id=manifest.package_mode,
        event_metadata={
            "package_mode": manifest.package_mode,
            "representative_doc": target_code,
            "size_bytes": pdf_res.size_bytes,
        },
    )
    db.commit()


@router.post(
    "/document-package/preview",
    response_class=Response,
    summary="Generar previsualización conjunta (PDF) del paquete documental de transporte",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_transport_package_combined(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.transport_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    pdf_res, manifest, target_code = _render_transport_package_pdf(payload, principal, db)

    response = build_pdf_preview_response(
        pdf_res.pdf_bytes,
        PACKAGE_PDF_FILENAME,
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Package-Mode": manifest.package_mode,
        },
    )

    _record_transport_package_event(
        db, principal, manifest, pdf_res, target_code, downloaded=False
    )

    return response


@router.post(
    "/document-package/pdf",
    response_class=Response,
    summary="Descargar previsualización conjunta (PDF) del paquete documental de transporte",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_transport_package_combined(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.transport_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Same combined PDF as the preview, delivered as an explicit download."""
    pdf_res, manifest, target_code = _render_transport_package_pdf(payload, principal, db)

    response = build_pdf_download_response(
        pdf_res.pdf_bytes,
        PACKAGE_PDF_FILENAME,
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Package-Mode": manifest.package_mode,
        },
    )

    _record_transport_package_event(
        db, principal, manifest, pdf_res, target_code, downloaded=True
    )

    return response
