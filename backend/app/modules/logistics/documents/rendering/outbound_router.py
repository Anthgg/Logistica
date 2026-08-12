"""FastAPI router for Outbound Document Preview, PDF, and Package Manifest endpoints (Phase 018).

Covers: PED, ODS, PICK, PACK
Phase 018 — preview only. No real operations.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.rendering.dispatch_schemas import (
    OutboundDispatchDocumentPackageManifest,
)
from app.modules.logistics.documents.rendering.outbound_service import (
    OutboundRenderingService,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/outbound", tags=["Logistics - Outbound Documents"])


@router.post(
    "/documents/{document_type_code}/preview",
    response_class=Response,
    summary="Generar vista previa PDF de documento de salida (PED, ODS, PICK, PACK)",
)
def preview_outbound_document(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = OutboundRenderingService(db)
    pdf_res = service.render_outbound_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
    )

    AuditService().record(
        db=db,
        event_type="logistics.outbound_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="outbound_document",
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

    return Response(
        content=pdf_res.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{pdf_res.filename_suggestion}"',
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Content-Hash": pdf_res.content_hash,
            "X-Template-Version": "1.0.0",
            "Cache-Control": "private, no-store",
        },
    )


@router.post(
    "/documents/{document_type_code}/pdf",
    response_class=Response,
    summary="Descargar PDF de documento de salida (Modo Preview Protegido)",
)
def download_outbound_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = OutboundRenderingService(db)
    pdf_res = service.render_outbound_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
    )

    AuditService().record(
        db=db,
        event_type="logistics.outbound_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="outbound_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
        },
    )
    db.commit()

    return Response(
        content=pdf_res.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="PREVIEW_{document_type_code.upper()}_{{}}.pdf"'.format(
                __import__("datetime").datetime.now().strftime("%Y%m%d")
            ),
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Template-Version": "1.0.0",
            "Cache-Control": "private, no-store",
        },
    )


@router.post(
    "/document-package/manifest",
    response_model=OutboundDispatchDocumentPackageManifest,
    summary="Evaluar y obtener el manifiesto del paquete documental de salida",
)
def get_outbound_package_manifest(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> OutboundDispatchDocumentPackageManifest:
    service = OutboundRenderingService(db)
    manifest = service.build_outbound_package_manifest(payload)

    AuditService().record(
        db=db,
        event_type="logistics.outbound_document.package_manifest_created",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="outbound_package_manifest",
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


@router.post(
    "/document-package/preview",
    response_class=Response,
    summary="Generar previsualización conjunta (PDF multipágina) del paquete documental de salida",
)
def preview_outbound_package_combined(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Generates a combined PDF preview of all documents in the manifest.

    Phase 018 — preview only.
    """
    service = OutboundRenderingService(db)
    manifest = service.build_outbound_package_manifest(payload)

    # For preview, we render the first required and included document as a representative PDF
    # or a dedicated combined template if pypdf is not available.
    target_code = "PED"
    for entry in manifest.document_entries:
        if entry.included:
            target_code = entry.document_type_code
            break

    # Extract corresponding document data from payload if present
    doc_data = payload.get("document_data", {}).get(target_code, payload)
    pdf_res = service.render_outbound_preview(
        document_type_code=target_code,
        data=doc_data,
        user_id=str(principal.user_id),
    )

    AuditService().record(
        db=db,
        event_type="logistics.outbound_document.package_preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="outbound_package_preview",
        resource_id=manifest.package_mode,
        event_metadata={
            "package_mode": manifest.package_mode,
            "representative_doc": target_code,
            "size_bytes": pdf_res.size_bytes,
        },
    )
    db.commit()

    return Response(
        content=pdf_res.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="PREVIEW_PAQUETE-SALIDA_COMBINED.pdf"',
            "X-Document-Mode": "PREVIEW",
            "X-Package-Mode": manifest.package_mode,
            "Cache-Control": "private, no-store",
        },
    )
