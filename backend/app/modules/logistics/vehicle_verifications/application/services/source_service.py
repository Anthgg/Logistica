"""VehicleVerificationSource Application Service (Phase 028)."""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    VehicleVerificationSourceDisabled,
    VehicleVerificationSourceNotAuthorized,
)
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import (
    VehicleVerificationProviderConfigurationModel,
    VehicleVerificationSourceModel,
)


class VehicleVerificationSourceService:
    def __init__(self, db: Session):
        self.db = db

    def seed_default_sources(self) -> List[VehicleVerificationSourceModel]:
        sources_def = [
            {
                "code": "SUNARP_REGISTRY",
                "name": "Superintendencia Nacional de los Registros Públicos",
                "authority": "SUNARP",
                "source_type": "SUNARP",
                "base_domain": "https://www.sunarp.gob.pe",
                "verification_domains": ["REGISTRY_IDENTITY", "REGISTERED_OWNER", "VEHICLE_CHARACTERISTICS", "LIENS_AND_ENCUMBRANCES"],
                "automation_mode": "MANUAL_ASSISTED",
                "authorization_status": "NOT_EVALUATED",
                "priority": 10,
            },
            {
                "code": "MTC_TRANSPORT",
                "name": "Ministerio de Transportes y Comunicaciones",
                "authority": "MTC",
                "source_type": "MTC",
                "base_domain": "https://www.gob.pe/mtc",
                "verification_domains": ["TRANSPORT_AUTHORIZATION", "CARRIER_AUTHORIZATION", "TECHNICAL_INSPECTION", "OPERATING_PERMIT"],
                "automation_mode": "MANUAL_ASSISTED",
                "authorization_status": "NOT_EVALUATED",
                "priority": 20,
            },
            {
                "code": "SBS_SOAT",
                "name": "Superintendencia de Banca, Seguros y AFP (SOAT/CAT)",
                "authority": "SBS",
                "source_type": "SBS",
                "base_domain": "https://www.sbs.gob.pe",
                "verification_domains": ["SOAT", "CAT", "VEHICLE_INSURANCE"],
                "automation_mode": "MANUAL_ASSISTED",
                "authorization_status": "NOT_EVALUATED",
                "priority": 30,
            },
            {
                "code": "AUTHORIZED_PROVIDER_FAKE",
                "name": "Proveedor de Verificación Vehicular Autorizado (Testing)",
                "authority": "PROVEEDOR_PRIVADO",
                "source_type": "AUTHORIZED_PROVIDER",
                "provider_code": "FAKE_AUTH_PROVIDER",
                "verification_domains": ["REGISTRY_IDENTITY", "REGISTERED_OWNER", "TECHNICAL_INSPECTION", "SOAT", "TRANSPORT_AUTHORIZATION"],
                "automation_mode": "API",
                "authorization_status": "AUTHORIZED",
                "authorization_reference": "CONTRATO-DEMO-2026-001",
                "priority": 5,
            },
        ]

        created = []
        for s in sources_def:
            existing = self.db.scalars(
                select(VehicleVerificationSourceModel).where(VehicleVerificationSourceModel.code == s["code"])
            ).first()

            if not existing:
                src = VehicleVerificationSourceModel(
                    id=uuid4(),
                    code=s["code"],
                    name=s["name"],
                    authority=s["authority"],
                    source_type=s["source_type"],
                    base_domain=s.get("base_domain"),
                    provider_code=s.get("provider_code"),
                    verification_domains=s["verification_domains"],
                    enabled=True,
                    automation_mode=s["automation_mode"],
                    authorization_status=s["authorization_status"],
                    authorization_reference=s.get("authorization_reference"),
                    priority=s["priority"],
                    status="ACTIVE",
                )
                self.db.add(src)
                created.append(src)

        self.db.commit()
        return created

    def get_source_by_code(self, code: str) -> VehicleVerificationSourceModel:
        src = self.db.scalars(
            select(VehicleVerificationSourceModel).where(VehicleVerificationSourceModel.code == code)
        ).first()
        if not src:
            raise HTTPException(status_code=404, detail=f"Fuente de verificación '{code}' no encontrada.")
        return src

    def list_sources(self, enabled_only: bool = False) -> List[VehicleVerificationSourceModel]:
        stmt = select(VehicleVerificationSourceModel)
        if enabled_only:
            stmt = stmt.where(and_(VehicleVerificationSourceModel.enabled == True, VehicleVerificationSourceModel.status == "ACTIVE"))
        return list(self.db.scalars(stmt.order_by(VehicleVerificationSourceModel.priority.asc())).all())

    def enable_source(self, source_id: UUID, actor_id: UUID) -> VehicleVerificationSourceModel:
        src = self.db.get(VehicleVerificationSourceModel, source_id)
        if not src:
            raise HTTPException(status_code=404, detail="Fuente de verificación no encontrada.")

        src.enabled = True
        src.status = "ACTIVE"
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.source_enabled",
                severity="high",
                actor_user_id=actor_id,
                resource_type="verification_source",
                resource_id=str(src.id),
                resource_code=src.code,
            ),
        )
        return src

    def disable_source(self, source_id: UUID, actor_id: UUID, reason: str = "") -> VehicleVerificationSourceModel:
        src = self.db.get(VehicleVerificationSourceModel, source_id)
        if not src:
            raise HTTPException(status_code=404, detail="Fuente de verificación no encontrada.")

        src.enabled = False
        src.status = "DISABLED"
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.source_disabled",
                severity="high",
                actor_user_id=actor_id,
                resource_type="verification_source",
                resource_id=str(src.id),
                resource_code=src.code,
                reason_text=reason,
            ),
        )
        return src
