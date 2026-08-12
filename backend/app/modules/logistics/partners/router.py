"""FastAPI REST endpoints for Phase 025 — Business Partners Master Data."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.partners.duplicate_detector import BusinessPartnerDuplicateDetection
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerRoleModel,
)
from app.modules.logistics.partners.partner_service import BusinessPartnerService
from app.modules.logistics.partners.schemas import (
    BusinessPartnerAddressCreateSchema,
    BusinessPartnerContactCreateSchema,
    BusinessPartnerCreateSchema,
    BusinessPartnerEvaluationCreateSchema,
    BusinessPartnerResponseSchema,
    BusinessPartnerRoleCreateSchema,
    DuplicateCheckRequestSchema,
)
from app.modules.logistics.principal import LogisticsPrincipal

router = APIRouter(prefix="/business-partners", tags=["Logistics - Business Partners (Phase 025)"])


def _resolve_org_id(principal: LogisticsPrincipal) -> UUID:
    if principal.default_organization_id:
        return UUID(principal.default_organization_id)
    if principal.organization_ids:
        return UUID(principal.organization_ids[0])
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="No se encontró una organización válida en el contexto de sesión.")


@router.post("", response_model=BusinessPartnerResponseSchema, status_code=status.HTTP_201_CREATED)
def create_partner(
    payload: BusinessPartnerCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = BusinessPartnerService(db)
    return service.create_partner(
        organization_id=org_id,
        legal_name=payload.legal_name,
        trade_name=payload.trade_name,
        person_type=payload.person_type,
        country_code=payload.country_code,
        tax_id_type=payload.tax_id_type,
        tax_id_value=payload.tax_id_value,
        roles=payload.roles,
        actor_id=principal.user_id,
    )


@router.get("", response_model=List[BusinessPartnerResponseSchema])
def list_partners(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    partner_status: Optional[str] = Query(None, alias="status"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    stmt = select(BusinessPartnerModel).where(
        BusinessPartnerModel.organization_id == org_id
    )
    if partner_status:
        stmt = stmt.where(BusinessPartnerModel.status == partner_status.upper())
    if search:
        stmt = stmt.where(
            (BusinessPartnerModel.legal_name.ilike(f"%{search}%"))
            | (BusinessPartnerModel.partner_code.ilike(f"%{search}%"))
        )
    if role:
        stmt = stmt.join(BusinessPartnerRoleModel).where(
            and_(
                BusinessPartnerRoleModel.role_type == role.upper(),
                BusinessPartnerRoleModel.status == "ACTIVE",
            )
        )
    partners = db.scalars(stmt.order_by(BusinessPartnerModel.created_at.desc())).all()
    return partners


@router.get("/{partner_id}", response_model=BusinessPartnerResponseSchema)
def get_partner(
    partner_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    return BusinessPartnerService(db).get_partner(partner_id, org_id)


@router.post("/{partner_id}/activate", response_model=BusinessPartnerResponseSchema)
def activate_partner(
    partner_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.activate")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    return BusinessPartnerService(db).activate_partner(partner_id, org_id, actor_id=principal.user_id)


@router.post("/{partner_id}/block", response_model=BusinessPartnerResponseSchema)
def block_partner(
    partner_id: UUID,
    reason: Optional[str] = Query(None),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.block")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    return BusinessPartnerService(db).block_partner(partner_id, org_id, actor_id=principal.user_id, reason=reason)


@router.post("/{partner_id}/roles")
def add_role(
    partner_id: UUID,
    payload: BusinessPartnerRoleCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partner_roles.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    role = BusinessPartnerService(db).add_role(partner_id, org_id, payload.role_type, actor_id=principal.user_id)
    return {"message": "Role added", "role_id": str(role.id), "role_type": role.role_type}


@router.post("/{partner_id}/addresses")
def add_address(
    partner_id: UUID,
    payload: BusinessPartnerAddressCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partner_addresses.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    addr = BusinessPartnerService(db).add_address(
        partner_id=partner_id,
        organization_id=org_id,
        address_line_1=payload.address_line_1,
        address_type=payload.address_type,
        district=payload.district,
        province=payload.province,
        department=payload.department,
        is_primary=payload.is_primary,
        actor_id=principal.user_id,
    )
    return {"message": "Address added", "address_id": str(addr.id)}


@router.post("/{partner_id}/contacts")
def add_contact(
    partner_id: UUID,
    payload: BusinessPartnerContactCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partner_contacts.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    contact = BusinessPartnerService(db).add_contact(
        partner_id=partner_id,
        organization_id=org_id,
        full_name=payload.full_name,
        contact_type=payload.contact_type,
        email=payload.email,
        phone=payload.phone,
        is_primary=payload.is_primary,
        actor_id=principal.user_id,
    )
    return {"message": "Contact added", "contact_id": str(contact.id)}


@router.post("/{partner_id}/evaluations")
def submit_evaluation(
    partner_id: UUID,
    payload: BusinessPartnerEvaluationCreateSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partner_evaluations.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    crit_list = [c.model_dump() for c in payload.criteria]
    ev = BusinessPartnerService(db).submit_evaluation(
        partner_id=partner_id,
        organization_id=org_id,
        role_type=payload.role_type,
        criteria_scores=crit_list,
        summary=payload.summary,
        actor_id=principal.user_id,
    )
    return {
        "evaluation_id": str(ev.id),
        "total_score": str(ev.total_score),
        "risk_level": ev.risk_level,
        "status": ev.status,
    }


@router.post("/duplicate-check")
def duplicate_check(
    payload: DuplicateCheckRequestSchema,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.business_partners.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    results = BusinessPartnerDuplicateDetection.find_duplicates(
        db,
        organization_id=org_id,
        tax_id_val=payload.tax_id_value,
        legal_name=payload.legal_name,
        trade_name=payload.trade_name,
    )
    return {"candidates": results}
