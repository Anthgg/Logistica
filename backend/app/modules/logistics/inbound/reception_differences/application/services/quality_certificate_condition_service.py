"""Phase 041. Quality certificate requirements and applicability conditions service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanCertificateNotFound,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityCertificateRequirementModel,
    QualityControlApplicabilityConditionModel,
    QualityControlDefinitionModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityCertificateService:
    def __init__(self, db: Session):
        self.db = db

    def get_certificate(self, certificate_id: UUID) -> QualityCertificateRequirementModel:
        cert = self.db.scalar(
            select(QualityCertificateRequirementModel).where(
                QualityCertificateRequirementModel.id == certificate_id,
            )
        )
        if not cert:
            raise QualityPlanCertificateNotFound("QualityPlanCertificateNotFound", f"Requisito de certificado {certificate_id} no encontrado", 404)
        return cert

    def list_certificates(self, control_id: UUID) -> list[QualityCertificateRequirementModel]:
        return list(
            self.db.scalars(
                select(QualityCertificateRequirementModel).where(
                    QualityCertificateRequirementModel.control_id == control_id,
                )
            )
        )

    def create_certificate(
        self,
        control_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityCertificateRequirementModel:
        ctrl = self.db.scalar(
            select(QualityControlDefinitionModel).where(QualityControlDefinitionModel.id == control_id)
        )
        if not ctrl:
            raise quality_plan_error("QualityPlanControlNotFound", f"Control {control_id} no encontrado", 404)

        cert = QualityCertificateRequirementModel(
            id=uuid4(),
            control_id=control_id,
            certificate_type=data["certificate_type"],
            document_type_id=data.get("document_type_id"),
            is_mandatory=data.get("is_mandatory", True),
            validity_days=data.get("validity_days"),
            requires_signature=data.get("requires_signature", False),
            metadata_schema=data.get("metadata_schema"),
            description=data.get("description"),
        )
        self.db.add(cert)
        self.db.flush()
        return cert

    def update_certificate(
        self,
        certificate_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityCertificateRequirementModel:
        cert = self.get_certificate(certificate_id)
        for field in ("certificate_type", "document_type_id", "is_mandatory", "validity_days", "requires_signature", "metadata_schema", "description"):
            if field in data and data[field] is not None:
                setattr(cert, field, data[field])
        self.db.flush()
        return cert

    def delete_certificate(self, certificate_id: UUID, principal: LogisticsPrincipal) -> None:
        cert = self.get_certificate(certificate_id)
        self.db.delete(cert)
        self.db.flush()


class QualityConditionService:
    def __init__(self, db: Session):
        self.db = db

    def get_condition(self, condition_id: UUID) -> QualityControlApplicabilityConditionModel:
        cond = self.db.scalar(
            select(QualityControlApplicabilityConditionModel).where(
                QualityControlApplicabilityConditionModel.id == condition_id,
            )
        )
        if not cond:
            raise quality_plan_error("QualityPlanConditionNotFound", f"Condición {condition_id} no encontrada", 404)
        return cond

    def list_conditions(self, control_id: UUID) -> list[QualityControlApplicabilityConditionModel]:
        return list(
            self.db.scalars(
                select(QualityControlApplicabilityConditionModel).where(
                    QualityControlApplicabilityConditionModel.control_id == control_id,
                )
            )
        )

    def create_condition(
        self,
        control_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityControlApplicabilityConditionModel:
        cond = QualityControlApplicabilityConditionModel(
            id=uuid4(),
            control_id=control_id,
            condition_type=data["condition_type"],
            condition_field=data["condition_field"],
            condition_operator=data["condition_operator"],
            condition_value=data["condition_value"],
            description=data.get("description"),
        )
        self.db.add(cond)
        self.db.flush()
        return cond

    def update_condition(
        self,
        condition_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityControlApplicabilityConditionModel:
        cond = self.get_condition(condition_id)
        for field in ("condition_type", "condition_field", "condition_operator", "condition_value", "description"):
            if field in data and data[field] is not None:
                setattr(cond, field, data[field])
        self.db.flush()
        return cond

    def delete_condition(self, condition_id: UUID, principal: LogisticsPrincipal) -> None:
        cond = self.get_condition(condition_id)
        self.db.delete(cond)
        self.db.flush()
