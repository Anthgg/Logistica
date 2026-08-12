"""FastAPI router for Document Series and Talonario endpoints (Phase 013)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.documents.series.series_schemas import (
    DocumentNumberResponse,
    DocumentSeriesCreateRequest,
    DocumentSeriesResponse,
    DocumentSeriesStatusChangeRequest,
    DocumentTalonarioCancelRequest,
    DocumentTalonarioCreateRequest,
    DocumentTalonarioManifestResponse,
    DocumentTalonarioResponse,
)
from app.modules.logistics.documents.series.series_service import DocumentSeriesService
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

router = APIRouter(prefix="/document-series", tags=["Logistics - Document Series"])


@router.post(
    "",
    response_model=DocumentSeriesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva serie documental para una sede y año",
)
def create_document_series(
    req: DocumentSeriesCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentSeriesResponse:
    service = DocumentSeriesService(db)
    res = service.create_series(principal.organization_id, req, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_series.created",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_series",
        resource_id=str(res.id),
        event_metadata={"prefix": res.prefix, "document_year": res.document_year},
    )
    db.commit()
    return res


@router.get(
    "",
    response_model=list[DocumentSeriesResponse],
    summary="Listar series documentales de la organización",
)
def list_document_series(
    status: str | None = None,
    branch_id: UUID | None = None,
    document_year: int | None = None,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentSeriesResponse]:
    service = DocumentSeriesService(db)
    series_list = service.series_repo.list(
        organization_id=principal.organization_id,
        status=status,
        branch_id=branch_id,
        document_year=document_year,
    )
    return [DocumentSeriesResponse.model_validate(s) for s in series_list]


@router.get(
    "/{series_id}",
    response_model=DocumentSeriesResponse,
    summary="Obtener serie documental por ID",
)
def get_document_series(
    series_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentSeriesResponse:
    service = DocumentSeriesService(db)
    series = service.series_repo.get_by_id(series_id)
    if not series or series.organization_id != principal.organization_id:
        raise HTTPException(status_code=404, detail="DocumentSeries not found")
    return DocumentSeriesResponse.model_validate(series)


@router.post(
    "/{series_id}/activate",
    response_model=DocumentSeriesResponse,
    summary="Activar serie documental",
)
def activate_document_series(
    series_id: UUID,
    req: DocumentSeriesStatusChangeRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentSeriesResponse:
    service = DocumentSeriesService(db)
    res = service.activate_series(series_id, req.reason, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_series.activated",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_series",
        resource_id=str(series_id),
        event_metadata={"reason": req.reason},
    )
    db.commit()
    return res


@router.post(
    "/{series_id}/suspend",
    response_model=DocumentSeriesResponse,
    summary="Suspender serie documental",
)
def suspend_document_series(
    series_id: UUID,
    req: DocumentSeriesStatusChangeRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentSeriesResponse:
    service = DocumentSeriesService(db)
    res = service.suspend_series(series_id, req.reason, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_series.suspended",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_series",
        resource_id=str(series_id),
        event_metadata={"reason": req.reason},
    )
    db.commit()
    return res


@router.post(
    "/{series_id}/close",
    response_model=DocumentSeriesResponse,
    summary="Cerrar serie documental al finalizar año o retiro de política",
)
def close_document_series(
    series_id: UUID,
    req: DocumentSeriesStatusChangeRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentSeriesResponse:
    service = DocumentSeriesService(db)
    res = service.close_series(series_id, req.reason, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_series.closed",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_series",
        resource_id=str(series_id),
        event_metadata={"reason": req.reason},
    )
    db.commit()
    return res


@router.post(
    "/{series_id}/talonarios",
    response_model=DocumentTalonarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar rango continuo y crear talonario digital",
)
def reserve_document_number_range(
    series_id: UUID,
    req: DocumentTalonarioCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTalonarioResponse:
    service = DocumentSeriesService(db)
    res = service.reserve_number_range(series_id, req, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_series.range_reserved",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_talonario",
        resource_id=str(res.id),
        event_metadata={"quantity": req.quantity, "talonario_code": res.talonario_code},
    )
    db.commit()
    return res


@router.get(
    "/{series_id}/talonarios",
    response_model=list[DocumentTalonarioResponse],
    summary="Listar talonarios de una serie documental",
)
def list_series_talonarios(
    series_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentTalonarioResponse]:
    service = DocumentSeriesService(db)
    t_list = service.talonario_repo.list_by_series(series_id)
    return [DocumentTalonarioResponse.model_validate(t) for t in t_list]


@router.get(
    "/{series_id}/numbers",
    response_model=list[DocumentNumberResponse],
    summary="Listar correlativos paginados de una serie",
)
def list_series_numbers(
    series_id: UUID,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentNumberResponse]:
    service = DocumentSeriesService(db)
    nums = service.number_repo.list_by_series(series_id, status=status, limit=limit, offset=offset)
    return [DocumentNumberResponse.model_validate(n) for n in nums]


# Router for Talonarios under /api/logistics/document-talonarios
talonarios_router = APIRouter(prefix="/document-talonarios", tags=["Logistics - Document Talonarios"])


@talonarios_router.get(
    "/{talonario_id}",
    response_model=DocumentTalonarioResponse,
    summary="Obtener talonario digital por ID",
)
def get_document_talonario(
    talonario_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTalonarioResponse:
    service = DocumentSeriesService(db)
    tal = service.talonario_repo.get_by_id(talonario_id)
    if not tal or tal.organization_id != principal.organization_id:
        raise HTTPException(status_code=404, detail="DocumentTalonario not found")
    return DocumentTalonarioResponse.model_validate(tal)


@talonarios_router.get(
    "/{talonario_id}/numbers",
    response_model=list[DocumentNumberResponse],
    summary="Listar números de un talonario digital",
)
def list_talonario_numbers(
    talonario_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> list[DocumentNumberResponse]:
    service = DocumentSeriesService(db)
    nums = service.number_repo.list_by_talonario(talonario_id)
    return [DocumentNumberResponse.model_validate(n) for n in nums]


@talonarios_router.get(
    "/{talonario_id}/manifest",
    response_model=DocumentTalonarioManifestResponse,
    summary="Obtener manifiesto JSON de un talonario digital",
)
def get_talonario_manifest(
    talonario_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTalonarioManifestResponse:
    service = DocumentSeriesService(db)
    return service.generate_manifest(talonario_id)


@talonarios_router.post(
    "/{talonario_id}/cancel",
    response_model=DocumentTalonarioResponse,
    summary="Cancelar talonario digital e invalidar números NO consumidos",
)
def cancel_document_talonario(
    talonario_id: UUID,
    req: DocumentTalonarioCancelRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> DocumentTalonarioResponse:
    service = DocumentSeriesService(db)
    res = service.cancel_talonario(talonario_id, req.reason, actor_id=principal.user_id)
    AuditService().record(
        db=db,
        event_type="logistics.document_talonario.cancelled",
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="document_talonario",
        resource_id=str(talonario_id),
        event_metadata={"reason": req.reason, "voided_numbers": res.voided_numbers},
    )
    db.commit()
    return res


from fastapi import Response
from app.modules.logistics.documents.application.export_service import DocumentExportService


@router.get(
    "/{series_id}/talonario.pdf",
    summary="Generar PDF del talonario asociado a una serie (Fase 020)",
)
def get_series_talonario_pdf(
    series_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    # Find first talonario for this series
    from app.modules.logistics.documents.series.series_models import DocumentTalonarioModel
    tal = db.scalars(
        select(DocumentTalonarioModel).where(DocumentTalonarioModel.series_id == series_id)
    ).first()
    if not tal:
        raise HTTPException(status_code=404, detail="No se encontraron talonarios asociados a esta serie.")

    service = DocumentExportService(db)
    pdf_bytes, filename = service.generate_talonario_pdf(tal.id, principal.user_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "private, no-store",
        },
    )


@talonarios_router.get(
    "/{talonario_id}/pdf",
    summary="Generar PDF de talonario específico (Fase 020)",
)
def get_talonario_pdf(
    talonario_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = DocumentExportService(db)
    pdf_bytes, filename = service.generate_talonario_pdf(talonario_id, principal.user_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "private, no-store",
        },
    )


@talonarios_router.post(
    "/{talonario_id}/exports",
    summary="Exportar talonario digital a formato ZIP (Fase 020)",
)
def export_talonario_to_zip(
    talonario_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.documents.read")),
    db: Session = Depends(get_db),
) -> Response:
    service = DocumentExportService(db)
    zip_bytes, filename = service.export_talonario_zip(talonario_id, principal.user_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "private, no-store",
        },
    )

