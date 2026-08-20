"""FastAPI REST Router for Phase 030 — Files and Evidence Centralization."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    require_logistics_principal,
    require_permission,
    resolve_organization_id,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.files.application.services.association_service import (
    FileAssociationService,
)
from app.modules.logistics.files.application.services.evidence_custody_service import (
    EvidenceCustodyService,
)
from app.modules.logistics.files.application.services.file_asset_service import (
    FileAssetService,
)
from app.modules.logistics.files.application.services.preview_download_service import (
    FilePreviewDownloadService,
)
from app.modules.logistics.files.application.services.retention_legal_hold_service import (
    RetentionLegalHoldService,
)
from app.modules.logistics.files.application.services.upload_session_service import (
    FileUploadSessionService,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    FileAssetType,
    FileClassification,
)
from app.modules.logistics.files.presentation.schemas.dto import (
    CustodyEventResponse,
    DeletionRequestCreateRequest,
    DeletionRequestResponse,
    EvidenceRegisterRequest,
    EvidenceResponse,
    FileAssetResponse,
    FileAssetUpdateRequest,
    FileAssociationCreateRequest,
    FileAssociationResponse,
    FileVersionResponse,
    LegalHoldApplyRequest,
    LegalHoldResponse,
    SignedUrlResponse,
    UploadSessionCreateRequest,
    UploadSessionFinalizeRequest,
    UploadSessionResponse,
)

router = APIRouter(prefix="/files", tags=["files"])


# --- UPLOAD SESSIONS ---

@router.post(
    "/upload-sessions",
    dependencies=[Depends(require_permission("logistics.files.upload"))],
    response_model=UploadSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sesión de carga de archivo",
)
def create_upload_session(
    payload: UploadSessionCreateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FileUploadSessionService(db)
    session = service.create_upload_session(
        organization_id=org_id,
        user_id=principal.user_id,
        expected_filename=payload.expected_filename,
        expected_size_bytes=payload.expected_size_bytes,
        declared_mime_type=payload.declared_mime_type,
        asset_type=FileAssetType(payload.asset_type.upper()),
        classification=FileClassification(payload.classification.upper()),
        intended_resource_type=payload.intended_resource_type,
        intended_resource_id=payload.intended_resource_id,
        intended_association_type=payload.intended_association_type,
        expected_sha256=payload.expected_sha256,
        correlation_id=x_correlation_id,
    )
    return UploadSessionResponse(
        id=session.id,
        organization_id=session.organization_id,
        expected_filename=session.expected_filename,
        expected_size_bytes=session.expected_size_bytes,
        declared_mime_type=session.declared_MIME_type,
        upload_mode=session.upload_mode,
        status=session.status,
        quarantine_object_key=session.quarantine_object_key,
        upload_target_url=f"file://{session.quarantine_object_key}",
        expires_at=session.expires_at,
        created_at=session.created_at,
    )


@router.post(
    "/upload-sessions/{session_id}/finalize",
    dependencies=[Depends(require_permission("logistics.files.upload"))],
    response_model=FileAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalizar sesión de carga",
)
def finalize_upload_session(
    session_id: UUID,
    payload: UploadSessionFinalizeRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    service = FileUploadSessionService(db)
    asset, _ = service.finalize_upload_session(
        session_id=session_id,
        user_id=principal.user_id,
        title=payload.title,
        correlation_id=x_correlation_id,
    )
    return asset


# --- FILE ASSETS ---

@router.get(
    "",
    response_model=List[FileAssetResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar archivos de la organización",
)
def list_files(
    asset_type: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    lifecycle_status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_organization_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal, x_organization_id)
    service = FileAssetService(db)
    items, _ = service.list_file_assets(
        organization_id=org_id,
        asset_type=asset_type,
        classification=classification,
        lifecycle_status=lifecycle_status,
        search_query=q,
        limit=limit,
        offset=offset,
    )
    return items


@router.get(
    "/{file_id}",
    response_model=FileAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de archivo por ID",
)
def get_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
):
    org_id = resolve_organization_id(principal)
    service = FileAssetService(db)
    return service.get_file_asset(file_id, org_id)


@router.patch(
    "/{file_id}",
    dependencies=[Depends(require_permission("logistics.files.update"))],
    response_model=FileAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar metadatos de archivo",
)
def update_file(
    file_id: UUID,
    payload: FileAssetUpdateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FileAssetService(db)
    classification = FileClassification(payload.classification.upper()) if payload.classification else None
    return service.update_file_asset_metadata(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        title=payload.title,
        description=payload.description,
        classification=classification,
        correlation_id=x_correlation_id,
    )


@router.get(
    "/{file_id}/versions",
    response_model=List[FileVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar versiones inmutables del archivo",
)
def get_file_versions(
    file_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
):
    org_id = resolve_organization_id(principal)
    service = FileAssetService(db)
    return service.get_file_versions(file_id, org_id)


@router.get(
    "/{file_id}/download",
    response_model=SignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener URL firmada para descarga",
)
def get_download_url(
    file_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FilePreviewDownloadService(db)
    signed_url, asset, version = service.get_download_access(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        correlation_id=x_correlation_id,
    )
    return SignedUrlResponse(
        url=signed_url.url,
        expires_at=signed_url.expires_at,
        file_id=asset.id,
        filename=version.sanitized_filename,
    )


@router.get(
    "/{file_id}/preview",
    response_model=SignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener URL firmada para vista previa",
)
def get_preview_url(
    file_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FilePreviewDownloadService(db)
    signed_url, asset, version = service.get_preview_access(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        correlation_id=x_correlation_id,
    )
    return SignedUrlResponse(
        url=signed_url.url,
        expires_at=signed_url.expires_at,
        file_id=asset.id,
        filename=version.sanitized_filename,
    )


@router.post(
    "/{file_id}/archive",
    dependencies=[Depends(require_permission("logistics.files.archive"))],
    response_model=FileAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Archivar archivo",
)
def archive_file(
    file_id: UUID,
    reason: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FileAssetService(db)
    return service.archive_file_asset(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        reason=reason,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/{file_id}/restore",
    dependencies=[Depends(require_permission("logistics.files.restore"))],
    response_model=FileAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Restaurar archivo archivado",
)
def restore_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FileAssetService(db)
    return service.restore_file_asset(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        correlation_id=x_correlation_id,
    )


# --- ASSOCIATIONS ---

@router.post(
    "/{file_id}/associations",
    dependencies=[Depends(require_permission("logistics.files.update"))],
    response_model=FileAssociationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asociar archivo a un recurso de dominio",
)
def associate_file(
    file_id: UUID,
    payload: FileAssociationCreateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = FileAssociationService(db)
    return service.associate_file(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        association_type=payload.association_type,
        is_primary=payload.is_primary,
        correlation_id=x_correlation_id,
    )


# --- EVIDENCE & CUSTODY ---

@router.get(
    "/evidence",
    response_model=List[EvidenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar registros de evidencia de la organización",
)
def list_evidence(
    evidence_type: Optional[str] = Query(None),
    subject_type: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    acceptance_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_organization_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal, x_organization_id)
    service = EvidenceCustodyService(db)
    items, _ = service.list_evidence(
        organization_id=org_id,
        evidence_type=evidence_type,
        subject_type=subject_type,
        subject_id=subject_id,
        status=status,
        acceptance_status=acceptance_status,
        limit=limit,
        offset=offset,
    )
    return items


@router.post(
    "/evidence",
    dependencies=[Depends(require_permission("logistics.files.evidence.create"))],
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evidencia formal",
)
def register_evidence(
    payload: EvidenceRegisterRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = EvidenceCustodyService(db)
    return service.register_evidence(
        organization_id=org_id,
        user_id=principal.user_id,
        file_asset_id=payload.file_asset_id,
        evidence_type=payload.evidence_type,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        description=payload.description,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/evidence/{evidence_id}/accept",
    dependencies=[Depends(require_permission("logistics.files.evidence.accept"))],
    response_model=EvidenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Aceptar evidencia inmutable",
)
def accept_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = EvidenceCustodyService(db)
    return service.accept_evidence(
        evidence_id=evidence_id,
        organization_id=org_id,
        user_id=principal.user_id,
        correlation_id=x_correlation_id,
    )


@router.get(
    "/evidence/{evidence_id}/custody-events",
    response_model=List[CustodyEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener eventos de cadena de custodia de evidencia",
)
def get_custody_events(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
):
    org_id = resolve_organization_id(principal)
    service = EvidenceCustodyService(db)
    return service.get_custody_events(evidence_id, org_id)


# --- LEGAL HOLDS & DELETION ---

@router.post(
    "/{file_id}/legal-holds",
    dependencies=[Depends(require_permission("logistics.files.legal_hold"))],
    response_model=LegalHoldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aplicar retención legal (Legal Hold)",
)
def apply_legal_hold(
    file_id: UUID,
    payload: LegalHoldApplyRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = RetentionLegalHoldService(db)
    return service.apply_legal_hold(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        reason=payload.reason,
        authority_reference=payload.authority_reference,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/{file_id}/request-deletion",
    dependencies=[Depends(require_permission("logistics.files.delete"))],
    response_model=DeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar eliminación controlada de archivo",
)
def request_deletion(
    file_id: UUID,
    payload: DeletionRequestCreateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_logistics_principal),
    x_correlation_id: Optional[str] = Header(None),
):
    org_id = resolve_organization_id(principal)
    service = RetentionLegalHoldService(db)
    return service.request_file_deletion(
        file_id=file_id,
        organization_id=org_id,
        user_id=principal.user_id,
        reason=payload.reason,
        deletion_basis=payload.deletion_basis,
        correlation_id=x_correlation_id,
    )


# Standalone evidence router for /logistics/evidence
#
# Reexpone los mismos handlers bajo un segundo prefijo. `add_api_route` no hereda las
# dependencias declaradas en `@router.post(...)`, así que cada ruta repite su guard:
# sin eso, la misma operación queda protegida por una ruta y abierta por la otra.
evidence_router = APIRouter(prefix="/evidence", tags=["evidence"])
evidence_router.add_api_route("", list_evidence, methods=["GET"], response_model=List[EvidenceResponse], status_code=status.HTTP_200_OK, summary="Listar registros de evidencia", dependencies=[Depends(require_permission("logistics.files.read"))])
evidence_router.add_api_route("", register_evidence, methods=["POST"], response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, summary="Registrar evidencia formal", dependencies=[Depends(require_permission("logistics.files.evidence.create"))])
evidence_router.add_api_route("/{evidence_id}/accept", accept_evidence, methods=["POST"], response_model=EvidenceResponse, status_code=status.HTTP_200_OK, summary="Aceptar evidencia inmutable", dependencies=[Depends(require_permission("logistics.files.evidence.accept"))])
evidence_router.add_api_route("/{evidence_id}/custody-events", get_custody_events, methods=["GET"], response_model=List[CustodyEventResponse], status_code=status.HTTP_200_OK, summary="Obtener eventos de cadena de custodia", dependencies=[Depends(require_permission("logistics.files.read"))])

