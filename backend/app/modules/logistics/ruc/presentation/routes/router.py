"""FastAPI REST router for Phase 026 (RUC Lookup & Integration)."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.ruc.application.services.import_service import RucRegistryImportService
from app.modules.logistics.ruc.application.services.lookup_service import RucLookupService
from app.modules.logistics.ruc.application.services.verification_service import (
    BusinessPartnerRucIntegrationService,
    RucAssistedVerificationService,
)
from app.modules.logistics.ruc.infrastructure.persistence.models import (
    RucDataSourceModel,
    RucDatasetVersionModel,
    RucImportJobModel,
)
from app.modules.logistics.ruc.presentation.schemas.dto import (
    ApplyRucDataToPartnerSchema,
    RucAssistedVerificationCreateSchema,
    RucImportJobRequestSchema,
    RucImportJobResponseSchema,
    RucLookupResponseSchema,
)

router = APIRouter(prefix="/ruc", tags=["Logistics - RUC Lookup & SUNAT Integration (Phase 026)"])


def _resolve_org_id(principal: LogisticsPrincipal) -> UUID:
    if principal.default_organization_id:
        return UUID(principal.default_organization_id)
    if principal.organization_ids:
        return UUID(principal.organization_ids[0])
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="No se encontró una organización válida en el contexto de sesión.")


@router.get("/{ruc}", response_model=RucLookupResponseSchema, summary="Consultar RUC exacto en padrón y fuentes activas")
def lookup_ruc(
    ruc: str,
    include_annexes: bool = Query(False),
    allow_provider: bool = Query(False),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_lookup.read")),
    db: Session = Depends(get_db),
):
    service = RucLookupService(db)
    return service.lookup_ruc(
        raw_ruc=ruc,
        include_annexes=include_annexes,
        allow_provider=allow_provider,
        actor_id=principal.user_id,
        correlation_id=principal.correlation_id,
    )


@router.get("/sources/health", summary="Consultar estado de fuentes de datos de RUC")
def get_sources_health(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_sources.read")),
    db: Session = Depends(get_db),
):
    sources = db.scalars(select(RucDataSourceModel)).all()
    return [
        {
            "code": s.code,
            "name": s.name,
            "source_type": s.source_type,
            "status": s.status,
            "last_successful_sync_at": s.last_successful_sync_at.isoformat() if s.last_successful_sync_at else None,
            "consecutive_failures": s.consecutive_failures,
        }
        for s in sources
    ]


@router.get("/datasets/current", summary="Consultar los datasets de RUC activos")
def get_current_datasets(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_datasets.read")),
    db: Session = Depends(get_db),
):
    datasets = db.scalars(select(RucDatasetVersionModel).where(RucDatasetVersionModel.status == "ACTIVE")).all()
    return [
        {
            "id": str(d.id),
            "dataset_type": d.dataset_type,
            "total_rows": d.total_rows,
            "fetched_at": d.fetched_at.isoformat() if d.fetched_at else None,
            "activated_at": d.activated_at.isoformat() if d.activated_at else None,
            "archive_hash": d.archive_hash,
        }
        for d in datasets
    ]


@router.post("/imports", response_model=RucImportJobResponseSchema, status_code=status.HTTP_202_ACCEPTED, summary="Iniciar trabajo de importación de padrón RUC")
def trigger_ruc_import(
    payload: RucImportJobRequestSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_imports.execute")),
    db: Session = Depends(get_db),
):
    service = RucRegistryImportService(db)
    job = service.create_import_job(
        dataset_type=payload.dataset_type,
        trigger_type="MANUAL",
        requested_by=principal.user_id,
        custom_url=payload.custom_url,
    )
    return job


@router.get("/imports/{job_id}", response_model=RucImportJobResponseSchema, summary="Consultar estado de un trabajo de importación")
def get_import_job_status(
    job_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_imports.read")),
    db: Session = Depends(get_db),
):
    job = db.get(RucImportJobModel, job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job de importación no encontrado.")
    return job


@router.post("/datasets/{dataset_id}/activate", summary="Activar de forma atómica una versión de dataset RUC (Step-Up)")
def activate_dataset(
    dataset_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_datasets.activate")),
    db: Session = Depends(get_db),
):
    service = RucRegistryImportService(db)
    dataset = service.activate_dataset(dataset_id, actor_id=principal.user_id)
    return {"message": "Dataset activado atómicamente", "dataset_id": str(dataset.id), "status": dataset.status}


@router.post("/datasets/{source_id}/rollback", summary="Rollback al dataset RUC inmediatamente anterior (Step-Up)")
def rollback_dataset(
    source_id: UUID,
    dataset_type: str = Query("RUC_GENERAL"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_datasets.rollback")),
    db: Session = Depends(get_db),
):
    service = RucRegistryImportService(db)
    previous = service.rollback_dataset(source_id, dataset_type, actor_id=principal.user_id)
    return {"message": "Rollback realizado exitosamente", "active_dataset_id": str(previous.id)}


@router.post("/assisted-verifications", summary="Registrar solicitud de validación asistida oficial")
def create_assisted_verification(
    payload: RucAssistedVerificationCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_verifications.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = RucAssistedVerificationService(db)
    record = service.create_assisted_verification(
        organization_id=org_id,
        ruc=payload.ruc,
        verification_reason=payload.verification_reason,
        source_reference=payload.source_reference,
        actor_id=principal.user_id,
        business_partner_id=payload.business_partner_id,
        observed_legal_name=payload.observed_legal_name,
        observed_status=payload.observed_status,
        observed_condition=payload.observed_condition,
        observed_ubigeo=payload.observed_ubigeo,
        observations=payload.observations,
    )
    return {"assisted_verification_id": str(record.id), "status": "MATCH_CONFIRMED", "confidence_level": record.confidence_level}


@router.post("/assisted-verifications/{verification_id}/approve", summary="Aprobar revisión asistida oficial (Step-Up)")
def approve_assisted_verification(
    verification_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.ruc_verifications.approve")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = RucAssistedVerificationService(db)
    record = service.approve_assisted_verification(verification_id, org_id, approver_id=principal.user_id)
    return {"assisted_verification_id": str(record.id), "approved_at": record.approved_at.isoformat(), "confidence_level": record.confidence_level}


@router.post("/business-partners/{partner_id}/verify-ruc", summary="Registrar verificación inmutable de RUC en un socio")
def verify_partner_ruc(
    partner_id: UUID,
    allow_provider: bool = Query(False),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.ruc_verify")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    partner_service = RucLookupService(db)
    # Fetch current RUC from partner identifier
    from app.modules.logistics.partners.models import BusinessPartnerIdentifierModel
    ident = db.scalars(
        select(BusinessPartnerIdentifierModel).where(
            and_(
                BusinessPartnerIdentifierModel.business_partner_id == partner_id,
                BusinessPartnerIdentifierModel.identifier_type == "RUC",
            )
        )
    ).first()

    if not ident:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El socio no tiene un identificador de tipo RUC registrado.")

    lookup = partner_service.lookup_ruc(ident.normalized_value, allow_provider=allow_provider, actor_id=principal.user_id)
    integration = BusinessPartnerRucIntegrationService(db)
    verif = integration.verify_partner_ruc(org_id, partner_id, lookup, actor_id=principal.user_id)

    return {
        "verification_id": str(verif.id),
        "ruc": verif.ruc,
        "verification_result": verif.verification_result,
        "verified_legal_name": verif.verified_legal_name,
        "confidence_level": verif.confidence_level,
        "status": verif.status,
    }


@router.post("/business-partners/{partner_id}/apply-ruc-data", summary="Aplicar datos verificados campo por campo a un socio (Step-Up)")
def apply_ruc_data_to_partner(
    partner_id: UUID,
    payload: ApplyRucDataToPartnerSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.ruc_apply")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    integration = BusinessPartnerRucIntegrationService(db)
    partner = integration.apply_verified_fields_to_partner(
        organization_id=org_id,
        partner_id=partner_id,
        verification_id=payload.verification_id,
        apply_legal_name=payload.apply_legal_name,
        apply_annex_as_candidate=payload.apply_annex_as_candidate,
        selected_annex_address=payload.selected_annex_address,
        actor_id=principal.user_id,
        reason=payload.reason,
    )
    return {
        "message": "Campos verificados de RUC aplicados exitosamente al socio",
        "partner_id": str(partner.id),
        "legal_name": partner.legal_name,
        "row_version": partner.row_version,
    }
