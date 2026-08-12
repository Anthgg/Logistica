"""Phase 041. Quality plan validation service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    ControlType,
    ToleranceType,
    SamplingType,
    CONTROL_TYPE_TOLERANCE_MAP,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanValidationFailed,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    validate_control_type_tolerance,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityPlanScopeModel,
    QualityControlDefinitionModel,
    QualityToleranceDefinitionModel,
    QualitySamplingPlanModel,
    QualityCertificateRequirementModel,
)


class QualityPlanValidationService:
    def __init__(self, db: Session):
        self.db = db

    def validate_plan(self, plan_id: UUID, organization_id: UUID) -> dict[str, Any]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise quality_plan_error("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)

        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        scopes = list(
            self.db.scalars(
                select(QualityPlanScopeModel).where(QualityPlanScopeModel.plan_id == plan_id)
            )
        )
        if not scopes:
            errors.append({"field": "scopes", "message": "El plan debe tener al menos un ámbito"})

        controls = list(
            self.db.scalars(
                select(QualityControlDefinitionModel).where(
                    QualityControlDefinitionModel.plan_id == plan_id,
                )
            )
        )

        mandatory_count = sum(1 for c in controls if c.is_mandatory)
        if mandatory_count == 0 and controls:
            warnings.append({"field": "controls", "message": "El plan no tiene controles obligatorios"})

        for ctrl in controls:
            tolerances = list(
                self.db.scalars(
                    select(QualityToleranceDefinitionModel).where(
                        QualityToleranceDefinitionModel.control_id == ctrl.id,
                    )
                )
            )
            if ctrl.is_mandatory and not tolerances:
                errors.append({
                    "field": f"control_{ctrl.control_code}",
                    "message": f"Control obligatorio '{ctrl.control_code}' no tiene definición de tolerancia",
                })

            for tol in tolerances:
                if not validate_control_type_tolerance(ctrl.control_type, tol.tolerance_type):
                    errors.append({
                        "field": f"tolerance_{tol.id}",
                        "message": f"Tipo de tolerancia '{tol.tolerance_type}' no es compatible con '{ctrl.control_type}'",
                    })

            samplings = list(
                self.db.scalars(
                    select(QualitySamplingPlanModel).where(
                        QualitySamplingPlanModel.control_id == ctrl.id,
                    )
                )
            )
            if ctrl.applies_to_sample and not samplings:
                warnings.append({
                    "field": f"sampling_{ctrl.control_code}",
                    "message": f"Control '{ctrl.control_code}' aplica a muestra pero no tiene plan de muestreo",
                })

            certificates = list(
                self.db.scalars(
                    select(QualityCertificateRequirementModel).where(
                        QualityCertificateRequirementModel.control_id == ctrl.id,
                    )
                )
            )
            if ctrl.control_type in (
                ControlType.CERTIFICATE_PRESENCE,
                ControlType.CERTIFICATE_VALIDITY_METADATA,
            ) and not certificates:
                errors.append({
                    "field": f"certificate_{ctrl.control_code}",
                    "message": f"Control de certificado '{ctrl.control_code}' no tiene requisitos de certificado",
                })

        is_valid = len(errors) == 0
        return {
            "plan_id": str(plan_id),
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "controls_count": len(controls),
            "scopes_count": len(scopes),
        }
