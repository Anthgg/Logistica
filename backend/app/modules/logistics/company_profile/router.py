"""FastAPI router for Company Profile, institutional versions, addresses, contacts, assets & signers (Phase 021)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.company_profile.address_contact_service import AddressContactService
from app.modules.logistics.company_profile.asset_service import AssetService
from app.modules.logistics.company_profile.company_profile_service import CompanyProfileService
from app.modules.logistics.company_profile.models import OrganizationDocumentSettingsModel, OrganizationProfileVersionModel
from app.modules.logistics.company_profile.numbering_policy_service import NumberingPolicyService
from app.modules.logistics.company_profile.schemas import (
    AssetUploadResponse,
    AuthorizedSignerCreate,
    AuthorizedSignerResponse,
    AuthorizedSignerUpdate,
    InstitutionalPreviewRequest,
    NumberingDisplayPolicyCreate,
    NumberingDisplayPolicyResponse,
    NumberingDisplayPolicyUpdate,
    OrganizationAddressCreate,
    OrganizationAddressResponse,
    OrganizationAddressUpdate,
    OrganizationAssetResponse,
    OrganizationContactCreate,
    OrganizationContactResponse,
    OrganizationContactUpdate,
    OrganizationDocumentSettingsResponse,
    OrganizationDocumentSettingsUpdate,
    OrganizationProfileCreate,
    OrganizationProfileResponse,
    OrganizationProfileUpdate,
    OrganizationProfileVersionResponse,
    SignerRevokeRequest,
    VersionActivateRequest,
)
from app.modules.logistics.company_profile.signer_service import SignerService
from app.modules.logistics.company_profile.snapshot_provider import InstitutionalSnapshotProvider
from app.modules.logistics.documents.application.lifecycle_service import DocumentLifecycleService
from app.modules.logistics.principal import LogisticsPrincipal

router = APIRouter(prefix="/company-profile", tags=["Logistics - Company Profile (Phase 021)"])


def _resolve_org_id(principal: LogisticsPrincipal) -> UUID:
    if principal.default_organization_id:
        return UUID(principal.default_organization_id)
    if principal.organization_ids:
        return UUID(principal.organization_ids[0])
    raise HTTPException(status_code=400, detail="No se encontró una organización válida en el contexto de sesión.")


# --- Profile Endpoints ---

@router.get("", response_model=OrganizationProfileResponse, summary="Obtener la ficha institucional (Fase 021)")
def get_company_profile(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.read")),
    db: Session = Depends(get_db),
) -> OrganizationProfileResponse:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    profile = service.get_profile_or_create_default(org_id, principal.user_id)
    return profile


@router.post("", response_model=OrganizationProfileResponse, summary="Inicializar la ficha institucional (Fase 021)")
def create_company_profile(
    req: OrganizationProfileCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.create")),
    db: Session = Depends(get_db),
) -> OrganizationProfileResponse:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    update_req = OrganizationProfileUpdate(**req.model_dump())
    return service.update_profile(org_id, update_req, principal.user_id)


@router.patch("", response_model=OrganizationProfileResponse, summary="Actualizar datos de la ficha institucional (Fase 021)")
def update_company_profile(
    req: OrganizationProfileUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.update")),
    db: Session = Depends(get_db),
) -> OrganizationProfileResponse:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    return service.update_profile(org_id, req, principal.user_id)


# --- Versioning Endpoints ---

@router.get("/versions", response_model=list[OrganizationProfileVersionResponse], summary="Listar versiones institucionales (Fase 021)")
def list_profile_versions(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.read_history")),
    db: Session = Depends(get_db),
) -> list[OrganizationProfileVersionResponse]:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    profile = service.get_profile_or_create_default(org_id, principal.user_id)
    return profile.versions


@router.post("/versions", response_model=OrganizationProfileVersionResponse, summary="Crear nueva versión borrador institucional (Fase 021)")
def create_profile_version(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.create")),
    db: Session = Depends(get_db),
) -> OrganizationProfileVersionResponse:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    return service.create_version(org_id, principal.user_id)


@router.post("/versions/{version_id}/activate", response_model=OrganizationProfileVersionResponse, summary="Activar versión institucional (Fase 021)")
def activate_profile_version(
    version_id: UUID,
    req: VersionActivateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.activate")),
    db: Session = Depends(get_db),
) -> OrganizationProfileVersionResponse:
    org_id = _resolve_org_id(principal)
    service = CompanyProfileService(db)
    return service.activate_version(org_id, version_id, req.reason, principal.user_id)


# --- Address Endpoints ---

@router.get("/addresses", response_model=list[OrganizationAddressResponse], summary="Listar direcciones institucionales (Fase 021)")
def list_addresses(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_addresses.read")),
    db: Session = Depends(get_db),
) -> list[OrganizationAddressResponse]:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.list_addresses(org_id)


@router.post("/addresses", response_model=OrganizationAddressResponse, summary="Crear dirección institucional (Fase 021)")
def create_address(
    req: OrganizationAddressCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_addresses.manage")),
    db: Session = Depends(get_db),
) -> OrganizationAddressResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.create_address(org_id, req, principal.user_id)


@router.patch("/addresses/{address_id}", response_model=OrganizationAddressResponse, summary="Actualizar dirección institucional (Fase 021)")
def update_address(
    address_id: UUID,
    req: OrganizationAddressUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_addresses.manage")),
    db: Session = Depends(get_db),
) -> OrganizationAddressResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.update_address(org_id, address_id, req, principal.user_id)


@router.post("/addresses/{address_id}/set-primary", response_model=OrganizationAddressResponse, summary="Establecer dirección principal (Fase 021)")
def set_primary_address(
    address_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_addresses.manage")),
    db: Session = Depends(get_db),
) -> OrganizationAddressResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.set_primary_address(org_id, address_id, principal.user_id)


# --- Contact Endpoints ---

@router.get("/contacts", response_model=list[OrganizationContactResponse], summary="Listar contactos institucionales (Fase 021)")
def list_contacts(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_contacts.read")),
    db: Session = Depends(get_db),
) -> list[OrganizationContactResponse]:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.list_contacts(org_id)


@router.post("/contacts", response_model=OrganizationContactResponse, summary="Crear contacto institucional (Fase 021)")
def create_contact(
    req: OrganizationContactCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_contacts.manage")),
    db: Session = Depends(get_db),
) -> OrganizationContactResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.create_contact(org_id, req, principal.user_id)


@router.patch("/contacts/{contact_id}", response_model=OrganizationContactResponse, summary="Actualizar contacto institucional (Fase 021)")
def update_contact(
    contact_id: UUID,
    req: OrganizationContactUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_contacts.manage")),
    db: Session = Depends(get_db),
) -> OrganizationContactResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.update_contact(org_id, contact_id, req, principal.user_id)


@router.post("/contacts/{contact_id}/set-primary", response_model=OrganizationContactResponse, summary="Establecer contacto principal (Fase 021)")
def set_primary_contact(
    contact_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_contacts.manage")),
    db: Session = Depends(get_db),
) -> OrganizationContactResponse:
    org_id = _resolve_org_id(principal)
    service = AddressContactService(db)
    return service.set_primary_contact(org_id, contact_id, principal.user_id)


# --- Asset Endpoints ---

@router.get("/assets", response_model=list[OrganizationAssetResponse], summary="Listar activos institucionales (Fase 021)")
def list_assets(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_assets.read")),
    db: Session = Depends(get_db),
) -> list[OrganizationAssetResponse]:
    org_id = _resolve_org_id(principal)
    service = AssetService(db)
    return service.list_assets(org_id)


@router.post("/assets/logo", response_model=AssetUploadResponse, summary="Subir logotipo institucional (Fase 021)")
async def upload_logo(
    file: UploadFile = File(...),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_assets.upload")),
    db: Session = Depends(get_db),
) -> AssetUploadResponse:
    org_id = _resolve_org_id(principal)
    service = AssetService(db)

    file_bytes = await file.read()
    asset = service.upload_asset(
        organization_id=org_id,
        file_bytes=file_bytes,
        filename=file.filename or "logo.png",
        asset_type="DOCUMENT_LOGO",
        actor_id=principal.user_id,
    )

    # Link to Document Settings automatically
    settings = db.scalars(
        select(OrganizationDocumentSettingsModel).where(OrganizationDocumentSettingsModel.organization_id == org_id)
    ).first()
    if settings:
        settings.document_logo_asset_id = asset.id
        db.flush()

    return AssetUploadResponse(
        asset_id=asset.id,
        asset_type=asset.asset_type,
        filename=asset.filename,
        size_bytes=asset.size_bytes,
        file_hash=asset.file_hash,
        status=asset.status,
        message="Logotipo cargado y sanitizado correctamente.",
    )


@router.get("/assets/{asset_id}/content", summary="Descargar contenido de imagen institucional (Fase 021)")
def get_asset_content(
    asset_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_assets.read")),
    db: Session = Depends(get_db),
) -> Response:
    org_id = _resolve_org_id(principal)
    service = AssetService(db)
    content, mime_type, filename = service.get_asset_content(org_id, asset_id)

    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f"inline; filename={filename}", "Cache-Control": "private, max-age=3600"},
    )


@router.post("/assets/{asset_id}/activate", response_model=OrganizationAssetResponse, summary="Activar activo institucional (Fase 021)")
def activate_asset(
    asset_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_assets.activate")),
    db: Session = Depends(get_db),
) -> OrganizationAssetResponse:
    org_id = _resolve_org_id(principal)
    service = AssetService(db)
    return service.activate_asset(org_id, asset_id, principal.user_id)


@router.post("/assets/{asset_id}/revoke", response_model=OrganizationAssetResponse, summary="Revocar activo institucional (Fase 021)")
def revoke_asset(
    asset_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_assets.revoke")),
    db: Session = Depends(get_db),
) -> OrganizationAssetResponse:
    org_id = _resolve_org_id(principal)
    service = AssetService(db)
    return service.revoke_asset(org_id, asset_id, principal.user_id)


# --- Authorized Signer Endpoints ---

@router.get("/signers", response_model=list[AuthorizedSignerResponse], summary="Listar firmantes autorizados (Fase 021)")
def list_signers(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.read")),
    db: Session = Depends(get_db),
) -> list[AuthorizedSignerResponse]:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.list_signers(org_id)


@router.post("/signers", response_model=AuthorizedSignerResponse, summary="Crear firmante autorizado (Fase 021)")
def create_signer(
    req: AuthorizedSignerCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.create")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.create_signer(org_id, req, principal.user_id)


@router.patch("/signers/{signer_id}", response_model=AuthorizedSignerResponse, summary="Actualizar firmante autorizado (Fase 021)")
def update_signer(
    signer_id: UUID,
    req: AuthorizedSignerUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.update")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.update_signer(org_id, signer_id, req, principal.user_id)


@router.post("/signers/{signer_id}/signature", response_model=AuthorizedSignerResponse, summary="Subir y asociar firma visual a firmante (Fase 021)")
async def upload_signer_signature(
    signer_id: UUID,
    file: UploadFile = File(...),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.update")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    asset_srv = AssetService(db)
    signer_srv = SignerService(db)

    file_bytes = await file.read()
    asset = asset_srv.upload_asset(
        organization_id=org_id,
        file_bytes=file_bytes,
        filename=file.filename or "firma_visual.png",
        asset_type="VISUAL_SIGNATURE",
        actor_id=principal.user_id,
    )

    update_req = AuthorizedSignerUpdate(signature_asset_id=asset.id)
    return signer_srv.update_signer(org_id, signer_id, update_req, principal.user_id)


@router.post("/signers/{signer_id}/activate", response_model=AuthorizedSignerResponse, summary="Activar firmante autorizado (Fase 021)")
def activate_signer(
    signer_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.activate")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.set_signer_status(org_id, signer_id, "ACTIVE", actor_id=principal.user_id)


@router.post("/signers/{signer_id}/suspend", response_model=AuthorizedSignerResponse, summary="Suspender firmante autorizado (Fase 021)")
def suspend_signer(
    signer_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.revoke")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.set_signer_status(org_id, signer_id, "SUSPENDED", actor_id=principal.user_id)


@router.post("/signers/{signer_id}/revoke", response_model=AuthorizedSignerResponse, summary="Revocar firmante autorizado (Fase 021)")
def revoke_signer(
    signer_id: UUID,
    req: SignerRevokeRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.authorized_signers.revoke")),
    db: Session = Depends(get_db),
) -> AuthorizedSignerResponse:
    org_id = _resolve_org_id(principal)
    service = SignerService(db)
    return service.set_signer_status(org_id, signer_id, "REVOKED", reason=req.reason, actor_id=principal.user_id)


# --- Numbering Policy Endpoints ---

@router.get("/numbering-policies", response_model=list[NumberingDisplayPolicyResponse], summary="Listar políticas de presentación de numeración (Fase 021)")
def list_numbering_policies(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.numbering_policies.read")),
    db: Session = Depends(get_db),
) -> list[NumberingDisplayPolicyResponse]:
    org_id = _resolve_org_id(principal)
    service = NumberingPolicyService(db)
    return service.list_policies(org_id)


@router.post("/numbering-policies", response_model=NumberingDisplayPolicyResponse, summary="Crear política de presentación de numeración (Fase 021)")
def create_numbering_policy(
    req: NumberingDisplayPolicyCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.numbering_policies.create")),
    db: Session = Depends(get_db),
) -> NumberingDisplayPolicyResponse:
    org_id = _resolve_org_id(principal)
    service = NumberingPolicyService(db)
    return service.create_policy(org_id, req, principal.user_id)


@router.post("/numbering-policies/preview", summary="Previsualizar formato de numeración sin reserva de correlativo (Fase 021)")
def preview_numbering_policy(
    doc_type_code: str = Query("PED", max_length=32),
    display_pattern: str = Query("{TYPE}-{SITE}-{YEAR}-{SEQUENCE}", max_length=128),
    sequence_padding: int = Query(6, ge=4, le=10),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.numbering_policies.read")),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    org_id = _resolve_org_id(principal)
    service = NumberingPolicyService(db)
    return service.preview_numbering_display(
        organization_id=org_id,
        doc_type_code=doc_type_code,
        display_pattern=display_pattern,
        sequence_padding=sequence_padding,
    )


# --- Institutional Preview Endpoint ---

def _render_institutional_document(
    req: InstitutionalPreviewRequest,
    principal: LogisticsPrincipal,
    db: Session,
) -> tuple[bytes, str]:
    """Render the institutional document merging company profile and signer.

    Shared by the preview and download endpoints so both deliver identical bytes
    and perform the draft resolution exactly once per request.
    """
    org_id = _resolve_org_id(principal)
    signer_srv = SignerService(db)

    # 1. Resolve or ensure valid branch for organization
    target_branch_id = req.branch_id
    if not target_branch_id:
        from app.models.branch import Branch
        branch_obj = db.scalars(
            select(Branch).where(Branch.organization_id == org_id).order_by(Branch.created_at.asc())
        ).first()
        if not branch_obj:
            # Auto-bootstrap default branch for organization if none exists
            branch_obj = Branch(
                organization_id=org_id,
                code="LIM-MAIN",
                name="Sede Principal Lima",
                status="active",
                timezone="America/Lima",
                address_text="Av. Principal 123, Lima, Perú",
            )
            db.add(branch_obj)
            db.flush()
        target_branch_id = branch_obj.id

    # 2. Determine document type code
    doc_type_code = req.doc_type_code or "AREC"
    from app.modules.logistics.documents.models import DocumentTypeModel
    dt = db.scalars(select(DocumentTypeModel).where(DocumentTypeModel.code == doc_type_code.upper())).first()
    if not dt:
        # Fallback to any active document type
        first_dt = db.scalars(select(DocumentTypeModel)).first()
        if first_dt:
            doc_type_code = first_dt.code

    # 3. Resolve signer if available
    resolved_signer = signer_srv.resolve_authorized_signer(
        organization_id=org_id,
        branch_id=target_branch_id,
        document_family=req.family or req.document_family or "INBOUND",
        document_type_code=doc_type_code,
        requested_signer_id=req.signer_id,
    )

    life_srv = DocumentLifecycleService(db)
    draft = life_srv.create_draft(
        organization_id=org_id,
        branch_id=target_branch_id,
        warehouse_id=None,
        doc_type_code=doc_type_code,
        source_resource_type="PREVIEW",
        source_resource_id=req.signer_id or UUID("00000000-0000-0000-0000-000000000000"),
        source_operation_id=UUID("00000000-0000-0000-0000-000000000000"),
        title=f"VISTA PREVIA INSTITUCIONAL {doc_type_code}",
        structured_data={
            "resolved_signer": resolved_signer,
            "custom_data": req.custom_data,
            "is_preview": True,
        },
        sensitivity="INTERNAL",
        actor_id=principal.user_id,
    )

    pdf_bytes, filename = life_srv.preview_document(draft.id, actor_id=principal.user_id)

    return pdf_bytes, filename


@router.post("/document-preview", summary="Previsualizar documento con ficha y firma institucional (Fase 021)", responses=PDF_RESPONSE_SCHEMA)
def preview_institutional_document(
    req: InstitutionalPreviewRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Renders document preview merging active company profile and authorized signer without reserving numbers."""
    pdf_bytes, filename = _render_institutional_document(req, principal, db)
    return build_pdf_preview_response(pdf_bytes, filename)


@router.post(
    "/document-preview.pdf",
    summary="Descargar documento con ficha y firma institucional (Fase 021)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_institutional_document(
    req: InstitutionalPreviewRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.company_profile.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Same institutional render as the preview, delivered as an explicit download."""
    pdf_bytes, filename = _render_institutional_document(req, principal, db)
    return build_pdf_download_response(pdf_bytes, filename)
