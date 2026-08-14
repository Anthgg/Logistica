"""FastAPI router for Document Instance lifecycle, exports, and packages (Phase 020)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
# Import authorization dependency from logistics auth_dependencies module
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.documents.models import DocumentInstanceModel, DocumentTypeModel
from app.modules.logistics.documents.schemas import (
    DocumentDraftCreate,
    DocumentDraftUpdate,
    DocumentIssueRequest,
    DocumentIssueResponse,
    DocumentSummaryResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentPrintIntentCreate,
    DocumentReprintRequest,
    DocumentReprintResponse,
    DocumentCancelRequest,
    DocumentCancelResponse,
    DocumentHistoryResponse,
    DocumentExportCreate,
    DocumentExportJobResponse,
    DocumentPackageResponse,
)
from app.modules.logistics.documents.application.lifecycle_service import DocumentLifecycleService
from app.modules.logistics.documents.application.export_service import DocumentExportService

router = APIRouter()


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Listar y filtrar documentos logísticos (Fase 020)",
)
def list_documents(
    search: str | None = None,
    document_code: str | None = None,
    document_type_code: str | None = None,
    family: str | None = None,
    status: str | None = None,
    branch_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    source_resource_type: str | None = None,
    source_resource_id: UUID | None = None,
    issued_by: UUID | None = None,
    created_by: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    has_reprints: bool | None = None,
    is_cancelled: bool | None = None,
    sensitivity: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    # Build query
    stmt = select(DocumentInstanceModel)
    if not principal.is_platform_admin and principal.organization_ids:
        stmt = stmt.where(DocumentInstanceModel.organization_id.in_([UUID(oid) for oid in principal.organization_ids]))

    # Apply filters
    if search:
        # Avoid full text search on large fields; simple prefix/exact match or like on title
        stmt = stmt.where(DocumentInstanceModel.title.ilike(f"%{search}%"))
    if document_code:
        stmt = stmt.where(DocumentInstanceModel.document_code == document_code)
    if document_type_code:
        # Join DocumentTypeModel
        stmt = stmt.join(DocumentTypeModel).where(DocumentTypeModel.code == document_type_code.upper())
    if family:
        stmt = stmt.join(DocumentTypeModel).where(DocumentTypeModel.family.has(code=family.upper()))
    if status:
        stmt = stmt.where(DocumentInstanceModel.status == status.upper())
    if branch_id:
        stmt = stmt.where(DocumentInstanceModel.branch_id == branch_id)
    if warehouse_id:
        stmt = stmt.where(DocumentInstanceModel.warehouse_id == warehouse_id)
    if source_resource_type:
        stmt = stmt.where(DocumentInstanceModel.source_resource_type == source_resource_type.upper())
    if source_resource_id:
        stmt = stmt.where(DocumentInstanceModel.source_resource_id == source_resource_id)
    if issued_by:
        stmt = stmt.where(DocumentInstanceModel.issued_by == issued_by)
    if created_by:
        stmt = stmt.where(DocumentInstanceModel.created_by == created_by)
    if sensitivity:
        stmt = stmt.where(DocumentInstanceModel.sensitivity == sensitivity.upper())

    if is_cancelled is not None:
        if is_cancelled:
            stmt = stmt.where(DocumentInstanceModel.status == "CANCELLED")
        else:
            stmt = stmt.where(DocumentInstanceModel.status != "CANCELLED")

    if has_reprints is not None:
        if has_reprints:
            stmt = stmt.where(DocumentInstanceModel.reprint_count > 0)
        else:
            stmt = stmt.where(DocumentInstanceModel.reprint_count == 0)

    # Sort
    col = getattr(DocumentInstanceModel, sort_by, DocumentInstanceModel.created_at)
    if sort_direction.lower() == "desc":
        stmt = stmt.order_by(col.desc())
    else:
        stmt = stmt.order_by(col.asc())

    # Count
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # Paginate
    items = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all())

    # Map to schema
    # Helper to build summaries
    from app.models.organization import Organization
    from app.models.branch import Branch
    from app.models.warehouse import Warehouse

    summaries = []
    for it in items:
        dt = db.get(DocumentTypeModel, it.document_type_id)
        br = db.get(Branch, it.branch_id)
        wh = db.get(Warehouse, it.warehouse_id) if it.warehouse_id else None

        # Resolve actions permission flags based on backend rules
        # Platform admin bypasses, otherwise evaluate permissions
        can_cancel = (it.status == "ISSUED") and (principal.role == "admin" or "logistics.documents.cancel" in principal.permissions)
        can_reprint = (it.status in ("ISSUED", "CANCELLED")) and (principal.role == "admin" or "logistics.documents.reprint" in principal.permissions)

        summaries.append(
            DocumentSummaryResponse(
                id=it.id,
                document_code=it.document_code,
                document_type_code=dt.code if dt else "UNKNOWN",
                document_type_name=dt.name if dt else "Documento",
                family=dt.family.code if (dt and dt.family) else "LOGISTICS",
                title=it.title,
                status=it.status,
                issued_at=it.issued_at,
                issued_by_summary={"id": str(it.issued_by)} if it.issued_by else None,
                branch_summary={"id": str(it.branch_id), "name": br.name if br else "Sede"},
                warehouse_summary={"id": str(it.warehouse_id), "name": wh.name if wh else "Almacén"} if wh else None,
                source_reference={"resource_type": it.source_resource_type, "resource_id": str(it.source_resource_id) if it.source_resource_id else None},
                reprint_count=it.reprint_count,
                print_request_count=it.print_request_count,
                sensitivity=it.sensitivity,
                can_preview=True,
                can_download=it.status in ("ISSUED", "CANCELLED"),
                can_print=it.status in ("ISSUED", "CANCELLED"),
                can_reprint=can_reprint,
                can_cancel=can_cancel,
                can_view_history=True,
                authoritative_artifact_status="ACTIVE" if it.status in ("ISSUED", "CANCELLED") else None,
            )
        )

    return DocumentListResponse(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear borrador de documento (Fase 020)",
)
def create_draft_document(
    req: DocumentDraftCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.preview")),
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    service = DocumentLifecycleService(db)
    inst = service.create_draft(
        organization_id=req.organization_id,
        branch_id=req.branch_id,
        warehouse_id=req.warehouse_id,
        doc_type_code=req.document_type_code,
        source_resource_type=req.source_resource_type,
        source_resource_id=req.source_resource_id,
        source_operation_id=req.source_operation_id,
        title=req.title,
        structured_data=req.structured_data,
        sensitivity=req.sensitivity,
        actor_id=principal.user_id,
    )
    db.commit()

    dt = db.get(DocumentTypeModel, inst.document_type_id)
    return DocumentDetailResponse(
        id=inst.id,
        document_code=inst.document_code,
        document_type_code=dt.code if dt else "UNKNOWN",
        document_type_name=dt.name if dt else "Documento",
        family=dt.family.code if (dt and dt.family) else "LOGISTICS",
        title=inst.title,
        status=inst.status,
        lifecycle_status=inst.lifecycle_status,
        source_resource_type=inst.source_resource_type,
        source_resource_id=inst.source_resource_id,
        source_operation_id=inst.source_operation_id,
        current_snapshot_id=inst.current_snapshot_id,
        reprint_count=inst.reprint_count,
        print_request_count=inst.print_request_count,
        sensitivity=inst.sensitivity,
        can_preview=True,
        can_download=False,
        can_print=False,
        can_reprint=False,
        can_cancel=False,
        can_view_history=True,
        branch_summary={"id": str(inst.branch_id), "name": "Sede"},
        source_reference={"resource_type": inst.source_resource_type, "resource_id": str(inst.source_resource_id) if inst.source_resource_id else None},
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


@router.put(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Actualizar borrador de documento (Fase 020)",
)
def update_draft_document(
    document_id: UUID,
    req: DocumentDraftUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.preview")),
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    service = DocumentLifecycleService(db)
    inst = service.update_draft(
        document_id=document_id,
        title=req.title,
        structured_data=req.structured_data,
        warehouse_id=req.warehouse_id,
        sensitivity=req.sensitivity,
        actor_id=principal.user_id,
    )
    db.commit()

    dt = db.get(DocumentTypeModel, inst.document_type_id)
    return DocumentDetailResponse(
        id=inst.id,
        document_code=inst.document_code,
        document_type_code=dt.code if dt else "UNKNOWN",
        document_type_name=dt.name if dt else "Documento",
        family=dt.family.code if (dt and dt.family) else "LOGISTICS",
        title=inst.title,
        status=inst.status,
        lifecycle_status=inst.lifecycle_status,
        source_resource_type=inst.source_resource_type,
        source_resource_id=inst.source_resource_id,
        source_operation_id=inst.source_operation_id,
        current_snapshot_id=inst.current_snapshot_id,
        reprint_count=inst.reprint_count,
        print_request_count=inst.print_request_count,
        sensitivity=inst.sensitivity,
        can_preview=True,
        can_download=False,
        can_print=False,
        can_reprint=False,
        can_cancel=False,
        can_view_history=True,
        branch_summary={"id": str(inst.branch_id), "name": "Sede"},
        source_reference={"resource_type": inst.source_resource_type, "resource_id": str(inst.source_resource_id) if inst.source_resource_id else None},
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Ver detalle de un documento logístico (Fase 020)",
)
def get_document_detail(
    document_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    service = DocumentLifecycleService(db)
    inst = service.get_document(document_id)

    # GCS security: Check horizontal organization matching
    if not principal.can_access_organization(inst.organization_id):
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este documento.")

    dt = db.get(DocumentTypeModel, inst.document_type_id)
    return DocumentDetailResponse(
        id=inst.id,
        document_code=inst.document_code,
        document_type_code=dt.code if dt else "UNKNOWN",
        document_type_name=dt.name if dt else "Documento",
        family=dt.family.code if (dt and dt.family) else "LOGISTICS",
        title=inst.title,
        status=inst.status,
        lifecycle_status=inst.lifecycle_status,
        source_resource_type=inst.source_resource_type,
        source_resource_id=inst.source_resource_id,
        source_operation_id=inst.source_operation_id,
        current_snapshot_id=inst.current_snapshot_id,
        reprint_count=inst.reprint_count,
        print_request_count=inst.print_request_count,
        sensitivity=inst.sensitivity,
        can_preview=True,
        can_download=inst.status in ("ISSUED", "CANCELLED"),
        can_print=inst.status in ("ISSUED", "CANCELLED"),
        can_reprint=(inst.status in ("ISSUED", "CANCELLED")),
        can_cancel=(inst.status == "ISSUED"),
        can_view_history=True,
        branch_summary={"id": str(inst.branch_id), "name": "Sede"},
        source_reference={"resource_type": inst.source_resource_type, "resource_id": str(inst.source_resource_id) if inst.source_resource_id else None},
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


@router.get(
    "/{document_id}/history",
    response_model=DocumentHistoryResponse,
    summary="Ver historial del ciclo de vida (Fase 020)",
)
def get_document_history(
    document_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentHistoryResponse:
    service = DocumentLifecycleService(db)
    inst = service.get_document(document_id)
    if inst.organization_id != principal.organization_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este documento.")

    history = service.get_history(document_id)
    return DocumentHistoryResponse(document_id=document_id, history=history)


@router.get(
    "/{document_id}/preview",
    summary="Generar o previsualizar PDF del documento (Fase 020)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_document(
    document_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.preview")),
    db: Session = Depends(get_db),
) -> Response:
    service = DocumentLifecycleService(db)
    pdf_bytes, filename = service.preview_document(document_id, principal.user_id)

    return build_pdf_preview_response(pdf_bytes, filename)


@router.get(
    "/{document_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
    summary="Descargar PDF del documento emitido (Fase 020)",
)
def download_document_pdf(
    document_id: UUID,
    original: bool = Query(default=False, description="Descargar el PDF original sin marcas si está anulado"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.download")),
    db: Session = Depends(get_db),
) -> Response:
    service = DocumentLifecycleService(db)
    inst = service.get_document(document_id)

    if not principal.can_access_organization(inst.organization_id):
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este documento.")

    # Anullment protection: if cancelled, downloading the original requires logistics.audit.read_sensitive
    if inst.status == "CANCELLED" and original:
        # Check permissions
        if principal.role != "admin" and "logistics.audit.read_sensitive" not in principal.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso de auditoría elevado para descargar el original de un documento anulado."
            )
        # Audit access to original
        service._write_audit(
            "logistics.document.original_accessed",
            principal.user_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            inst.document_code,
        )

    _, artifact, pdf_bytes = service.get_downloadable_pdf(
        document_id,
        principal.user_id,
        original=original,
    )

    return build_pdf_download_response(pdf_bytes, artifact.filename)


@router.post(
    "/{document_id}/issue",
    response_model=DocumentIssueResponse,
    summary="Emitir documento oficial (Fase 020)",
)
def issue_document(
    document_id: UUID,
    req: DocumentIssueRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.issue")),
    db: Session = Depends(get_db),
) -> DocumentIssueResponse:
    # Obtain idempotency key from correlation_id or reason
    idempotency_key = principal.correlation_id
    service = DocumentLifecycleService(db)
    inst = service.issue_document(document_id, idempotency_key, principal.user_id)
    db.commit()

    from app.modules.logistics.documents.models import DocumentArtifactModel
    art = db.get(DocumentArtifactModel, inst.authoritative_artifact_id)

    return DocumentIssueResponse(
        document_id=inst.id,
        document_code=inst.document_code or "",
        status=inst.status,
        issued_at=inst.issued_at or utc_now(),
        authoritative_artifact_id=inst.authoritative_artifact_id or document_id,
        checksum=art.file_hash if art else "",
    )


@router.post(
    "/{document_id}/print-events",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registrar intención de impresión (Fase 020)",
)
def register_print_intent(
    document_id: UUID,
    req: DocumentPrintIntentCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> None:
    service = DocumentLifecycleService(db)
    service.register_print_intent(
        document_id=document_id,
        actor_id=principal.user_id,
        reason=req.reason,
        client_context=req.client_context,
    )
    db.commit()


@router.post(
    "/{document_id}/reprint",
    response_model=DocumentReprintResponse,
    summary="Reimprimir documento emitido (Fase 020)",
)
def reprint_document(
    document_id: UUID,
    req: DocumentReprintRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.reprint")),
    db: Session = Depends(get_db),
) -> DocumentReprintResponse:
    # Use correlation_id as idempotency key
    idempotency_key = principal.correlation_id
    service = DocumentLifecycleService(db)
    rep = service.reprint_document(document_id, req.reason, principal.user_id, idempotency_key)
    db.commit()

    return DocumentReprintResponse(
        document_id=document_id,
        copy_number=rep.copy_number,
        artifact_id=rep.generated_artifact_id,
        download_url=f"/api/logistics/documents/{document_id}/pdf?copy={rep.copy_number}",
        generated_at=rep.requested_at,
    )


@router.post(
    "/{document_id}/cancel",
    response_model=DocumentCancelResponse,
    summary="Anular documento emitido (Fase 020)",
)
def cancel_document(
    document_id: UUID,
    req: DocumentCancelRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.cancel")),
    db: Session = Depends(get_db),
) -> DocumentCancelResponse:
    # Use correlation_id as idempotency key
    idempotency_key = principal.correlation_id
    service = DocumentLifecycleService(db)
    cxl = service.cancel_document(document_id, req.reason, principal.user_id, idempotency_key)
    db.commit()

    inst = service.get_document(document_id)
    return DocumentCancelResponse(
        document_id=document_id,
        status=inst.status,
        cancelled_at=cxl.cancelled_at,
        cancelled_by=cxl.cancelled_by,
        reason=cxl.reason,
    )


@router.post(
    "/export",
    response_model=DocumentExportJobResponse,
    summary="Exportación múltiple a ZIP (Fase 020)",
)
def export_documents(
    req: DocumentExportCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.export")),
    db: Session = Depends(get_db),
) -> DocumentExportJobResponse:
    service = DocumentExportService(db)
    job = service.create_export_job(
        organization_id=UUID(principal.default_organization_id) if principal.default_organization_id else (UUID(principal.organization_ids[0]) if principal.organization_ids else uuid4()),
        document_ids=req.document_ids,
        export_format=req.export_format,
        include_manifest=req.include_manifest,
        include_checksums=req.include_checksums,
        reason=req.reason,
        actor_id=principal.user_id,
    )
    db.commit()

    download_url = f"/api/logistics/document-exports/{job.id}/download" if job.status == "READY" else None

    return DocumentExportJobResponse(
        job_id=job.id,
        status=job.status,
        total_items=job.total_items,
        processed_items=job.processed_items,
        failed_items=job.failed_items,
        expires_at=job.expires_at,
        polling_url=f"/api/logistics/document-exports/{job.id}",
        download_url=download_url,
    )


def create_router() -> APIRouter:
    return router


def create_packages_router() -> APIRouter:
    p_router = APIRouter(prefix="/document-packages", tags=["Logistics - Document Packages"])

    @p_router.get(
        "/{operation_type}/{operation_id}.zip",
        summary="Descargar paquete de documentos por operación (Fase 020)",
    )
    def download_operation_package(
        operation_type: str,
        operation_id: UUID,
        principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
        db: Session = Depends(get_db),
    ) -> Response:
        service = DocumentExportService(db)
        org_id = UUID(principal.default_organization_id) if principal.default_organization_id else (UUID(principal.organization_ids[0]) if principal.organization_ids else uuid4())
        zip_bytes, filename = service.get_operation_package(
            org_id, operation_type, operation_id, principal.user_id
        )

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "private, no-store",
            },
        )

    @p_router.get(
        "/{operation_id}.zip",
        summary="Descargar paquete de documentos por ID (Fase 020)",
    )
    def download_operation_package_short(
        operation_id: UUID,
        principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
        db: Session = Depends(get_db),
    ) -> Response:
        # Default operation type to RECEPTION
        service = DocumentExportService(db)
        org_id = UUID(principal.default_organization_id) if principal.default_organization_id else (UUID(principal.organization_ids[0]) if principal.organization_ids else uuid4())
        zip_bytes, filename = service.get_operation_package(
            org_id, "RECEPTION", operation_id, principal.user_id
        )

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "private, no-store",
            },
        )

    return p_router
