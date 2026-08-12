"""FastAPI router for delivery document rendering (Phase 019)."""

from typing import Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.documents.rendering.delivery_service import DeliveryRenderingService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/delivery", tags=["Logistics Delivery Documents"])


@router.post(
    "/documents/{document_type_code}/preview",
    response_class=Response,
    summary="Previsualizar PDF de documento de entrega (Modo Preview Protegido)",
)
def preview_delivery_document(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.delivery_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    sensitive_read = principal.has_permission("logistics.delivery_documents.read_sensitive")
    service = DeliveryRenderingService(db)
    
    pdf_res = service.render_delivery_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        sensitive_read=sensitive_read,
    )

    AuditService().record(
        db=db,
        event_type="logistics.delivery_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="delivery_document",
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
    summary="Descargar PDF de documento de entrega (Modo Preview Protegido)",
)
def download_delivery_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.delivery_documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    sensitive_read = principal.has_permission("logistics.delivery_documents.read_sensitive")
    service = DeliveryRenderingService(db)
    
    pdf_res = service.render_delivery_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        sensitive_read=sensitive_read,
    )

    AuditService().record(
        db=db,
        event_type="logistics.delivery_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="delivery_document",
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
