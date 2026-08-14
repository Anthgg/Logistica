"""FastAPI router for Inventory Document Preview, PDF, and Package Manifest endpoints (Phase 017).

Covers: EUB, PUT, MOV, AJI, CNT, ADI, TRA, CRT
Phase 017 — preview only. No real inventory operations.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.rendering.inventory_schemas import (
    InventoryDocumentPackageManifest,
)
from app.modules.logistics.documents.rendering.inventory_service import (
    InventoryRenderingService,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.documents.rendering.filenames import preview_pdf_filename
from app.services.audit_service import AuditService

router = APIRouter(prefix="/inventory", tags=["Logistics - Inventory Documents"])


@router.post(
    "/documents/{document_type_code}/preview",
    response_class=Response,
    summary="Generar vista previa PDF de documento de inventario (EUB, PUT, MOV, AJI, CNT, ADI, TRA, CRT)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_inventory_document(
    document_type_code: str,
    payload: dict[str, Any],
    blind_count_mode: bool = Query(default=False, description="Si True y doc_type=CNT, oculta cantidades teóricas"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = InventoryRenderingService(db)
    pdf_res = service.render_inventory_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        blind_count_mode=blind_count_mode,
    )

    AuditService().record(
        db=db,
        event_type="logistics.inventory_document.preview_rendered",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="inventory_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "renderer_name": pdf_res.renderer_name,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
            "blind_count_mode": blind_count_mode,
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
            "X-Template-Version": "1.0.0",
        },
    )


@router.post(
    "/documents/{document_type_code}/pdf",
    response_class=Response,
    summary="Descargar PDF de documento de inventario (Modo Preview Protegido)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_inventory_document_pdf(
    document_type_code: str,
    payload: dict[str, Any],
    blind_count_mode: bool = Query(default=False, description="Si True y doc_type=CNT, oculta cantidades teóricas"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = InventoryRenderingService(db)
    pdf_res = service.render_inventory_preview(
        document_type_code=document_type_code,
        data=payload,
        user_id=str(principal.user_id),
        blind_count_mode=blind_count_mode,
    )

    AuditService().record(
        db=db,
        event_type="logistics.inventory_document.preview_downloaded",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="inventory_document",
        resource_id=document_type_code.upper(),
        event_metadata={
            "document_type_code": document_type_code.upper(),
            "size_bytes": pdf_res.size_bytes,
            "file_hash": pdf_res.file_hash,
            "preview_mode": True,
        },
    )
    db.commit()

    return build_pdf_download_response(
        pdf_res.pdf_bytes,
        preview_pdf_filename(document_type_code),
        extra_headers={
            "X-Document-Mode": "PREVIEW",
            "X-Document-Type": document_type_code.upper(),
            "X-Template-Version": "1.0.0",
        },
    )


@router.post(
    "/document-package/manifest",
    response_model=InventoryDocumentPackageManifest,
    summary="Evaluar y obtener el manifiesto del paquete documental de inventario",
)
def get_inventory_package_manifest(
    payload: dict[str, Any],
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> InventoryDocumentPackageManifest:
    service = InventoryRenderingService(db)
    manifest = service.build_inventory_package_manifest(payload)

    AuditService().record(
        db=db,
        event_type="logistics.inventory_document.package_manifest_created",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="inventory_package_manifest",
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
