"""Shared tenant, normalization, snapshot, audit and outbox helpers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeNotFound,
    ArrivalNoticePurchaseOrderInvalid,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeModel,
    ArrivalNoticeOutboxEventModel,
)
from app.modules.logistics.partners.models import BusinessPartnerModel, BusinessPartnerRoleModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def json_safe(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (UUID, date, datetime, time)):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def content_hash(payload: dict) -> str:
    encoded = json.dumps(json_safe(payload), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper().strip())


def normalize_document_reference(series: str | None, number: str) -> str:
    source = "-".join(part for part in (series, number) if part)
    return re.sub(r"[^A-Z0-9]", "", source.upper().strip())


def get_notice_for_org(
    db: Session,
    notice_id: UUID,
    organization_id: UUID,
    *,
    lock: bool = False,
) -> ArrivalNoticeModel:
    stmt = select(ArrivalNoticeModel).where(
        ArrivalNoticeModel.id == notice_id,
        ArrivalNoticeModel.organization_id == organization_id,
    )
    if lock:
        stmt = stmt.with_for_update()
    notice = db.scalar(stmt)
    if notice is None:
        raise ArrivalNoticeNotFound("El aviso de llegada no existe.")
    return notice


def get_warehouse_for_org(
    db: Session,
    warehouse_id: UUID,
    organization_id: UUID,
) -> Warehouse:
    warehouse = db.scalar(
        select(Warehouse).where(
            Warehouse.id == warehouse_id,
            Warehouse.organization_id == organization_id,
        )
    )
    if warehouse is None or not warehouse.is_active or not warehouse.receiving_enabled:
        raise ArrivalNoticePurchaseOrderInvalid(
            "El almacén no existe, no pertenece a la organización o no recibe carga."
        )
    return warehouse


def get_partner_with_role(
    db: Session,
    partner_id: UUID,
    organization_id: UUID,
    role_type: str,
) -> tuple[BusinessPartnerModel, BusinessPartnerRoleModel]:
    partner = db.scalar(
        select(BusinessPartnerModel).where(
            BusinessPartnerModel.id == partner_id,
            BusinessPartnerModel.organization_id == organization_id,
        )
    )
    if partner is None:
        raise ArrivalNoticePurchaseOrderInvalid("El socio de negocio no existe.")
    role = db.scalar(
        select(BusinessPartnerRoleModel).where(
            BusinessPartnerRoleModel.business_partner_id == partner.id,
            BusinessPartnerRoleModel.role_type == role_type,
            BusinessPartnerRoleModel.status == "ACTIVE",
        )
    )
    if role is None:
        raise ArrivalNoticePurchaseOrderInvalid(
            f"El socio de negocio no tiene el rol {role_type} activo."
        )
    if partner.status in {"BLOCKED", "ARCHIVED"} or partner.lifecycle_status != "ACTIVE":
        raise ArrivalNoticePurchaseOrderInvalid(
            f"El socio de negocio con rol {role_type} no está operativo."
        )
    return partner, role


def partner_snapshot(partner: BusinessPartnerModel) -> dict:
    return {
        "id": str(partner.id),
        "partner_code": partner.partner_code,
        "legal_name": partner.legal_name,
        "trade_name": partner.trade_name,
        "country_code": partner.country_code,
        "status": partner.status,
        "lifecycle_status": partner.lifecycle_status,
        "captured_at": utc_now().isoformat(),
    }


def write_audit(
    db: Session,
    *,
    event_code: str,
    actor_user_id: UUID | None,
    organization_id: UUID,
    resource_type: str,
    resource_id: UUID,
    branch_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    session_id: UUID | None = None,
    correlation_id: str | None = None,
    previous_data: dict | None = None,
    new_data: dict | None = None,
    reason: str | None = None,
    metadata: dict | None = None,
) -> None:
    audit_service.write_event(
        db,
        AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            session_id=session_id,
            correlation_id=correlation_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            previous_data=json_safe(previous_data),
            new_data=json_safe(new_data),
            reason_text=reason,
            metadata=json_safe(metadata),
            source_module="logistics.inbound",
            source_service="phase_036",
        ),
    )


def enqueue_event(
    db: Session,
    *,
    organization_id: UUID,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict,
    deduplication_key: str,
) -> ArrivalNoticeOutboxEventModel:
    event = ArrivalNoticeOutboxEventModel(
        organization_id=organization_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=json_safe(payload),
        deduplication_key=deduplication_key,
    )
    db.add(event)
    return event
