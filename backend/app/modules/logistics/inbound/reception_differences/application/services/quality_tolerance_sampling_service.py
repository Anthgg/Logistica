"""Phase 041. Quality tolerance and sampling management service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    ToleranceType,
    SamplingType,
    CONTROL_TYPE_TOLERANCE_MAP,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanToleranceNotFound,
    QualityPlanSamplingNotFound,
    QualityPlanToleranceTypeInvalid,
    QualityPlanToleranceValueInvalid,
    QualityPlanSamplingTypeInvalid,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    validate_control_type_tolerance,
    validate_tolerance_values,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityToleranceDefinitionModel,
    QualitySamplingPlanModel,
    QualityControlDefinitionModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityToleranceService:
    def __init__(self, db: Session):
        self.db = db

    def get_tolerance(self, tolerance_id: UUID, organization_id: UUID) -> QualityToleranceDefinitionModel:
        tol = self.db.scalar(
            select(QualityToleranceDefinitionModel)
            .join(QualityControlDefinitionModel)
            .where(
                QualityToleranceDefinitionModel.id == tolerance_id,
            )
        )
        if not tol:
            raise QualityPlanToleranceNotFound("QualityPlanToleranceNotFound", f"Tolerancia {tolerance_id} no encontrada", 404)
        return tol

    def list_tolerances(self, control_id: UUID) -> list[QualityToleranceDefinitionModel]:
        return list(
            self.db.scalars(
                select(QualityToleranceDefinitionModel).where(
                    QualityToleranceDefinitionModel.control_id == control_id,
                )
            )
        )

    def create_tolerance(
        self,
        control_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityToleranceDefinitionModel:
        ctrl = self.db.scalar(
            select(QualityControlDefinitionModel).where(QualityControlDefinitionModel.id == control_id)
        )
        if not ctrl:
            raise quality_plan_error("QualityPlanControlNotFound", f"Control {control_id} no encontrado", 404)

        tolerance_type = data.get("tolerance_type")
        valid_types = [t.value for t in ToleranceType]
        if tolerance_type not in valid_types:
            raise QualityPlanToleranceTypeInvalid(
                "QualityPlanToleranceTypeInvalid",
                f"Tipo de tolerancia '{tolerance_type}' no es válido",
                400,
            )

        if not validate_control_type_tolerance(ctrl.control_type, tolerance_type):
            raise QualityPlanToleranceTypeInvalid(
                "QualityPlanToleranceTypeInvalid",
                f"El tipo de tolerancia '{tolerance_type}' no es compatible con el control '{ctrl.control_type}'",
                400,
            )

        tol = QualityToleranceDefinitionModel(
            id=uuid4(),
            control_id=control_id,
            tolerance_type=tolerance_type,
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            target_value=data.get("target_value"),
            absolute_deviation=data.get("absolute_deviation"),
            percentage_deviation=data.get("percentage_deviation"),
            valid_options=data.get("valid_options"),
            default_value=data.get("default_value"),
            unit_code=data.get("unit_code"),
            description=data.get("description"),
        )
        self.db.add(tol)
        self.db.flush()
        return tol

    def update_tolerance(
        self,
        tolerance_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityToleranceDefinitionModel:
        tol = self.get_tolerance(tolerance_id, None)
        for field in ("min_value", "max_value", "target_value", "absolute_deviation", "percentage_deviation", "valid_options", "default_value", "unit_code", "description"):
            if field in data and data[field] is not None:
                setattr(tol, field, data[field])
        self.db.flush()
        return tol

    def delete_tolerance(self, tolerance_id: UUID, principal: LogisticsPrincipal) -> None:
        tol = self.get_tolerance(tolerance_id, None)
        self.db.delete(tol)
        self.db.flush()


class QualitySamplingService:
    def __init__(self, db: Session):
        self.db = db

    def get_sampling(self, sampling_id: UUID) -> QualitySamplingPlanModel:
        sp = self.db.scalar(
            select(QualitySamplingPlanModel).where(QualitySamplingPlanModel.id == sampling_id)
        )
        if not sp:
            raise QualityPlanSamplingNotFound("QualityPlanSamplingNotFound", f"Muestreo {sampling_id} no encontrado", 404)
        return sp

    def list_samplings(self, control_id: UUID) -> list[QualitySamplingPlanModel]:
        return list(
            self.db.scalars(
                select(QualitySamplingPlanModel).where(QualitySamplingPlanModel.control_id == control_id)
            )
        )

    def create_sampling(
        self,
        control_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualitySamplingPlanModel:
        sampling_type = data.get("sampling_type")
        valid_types = [t.value for t in SamplingType]
        if sampling_type not in valid_types:
            raise QualityPlanSamplingTypeInvalid(
                "QualityPlanSamplingTypeInvalid",
                f"Tipo de muestreo '{sampling_type}' no es válido",
                400,
            )

        sp = QualitySamplingPlanModel(
            id=uuid4(),
            control_id=control_id,
            sampling_type=sampling_type,
            fixed_count=data.get("fixed_count"),
            percentage=data.get("percentage"),
            minimum_count=data.get("minimum_count"),
            package_level=data.get("package_level"),
            lot_level=data.get("lot_level"),
            custom_formula=data.get("custom_formula"),
            description=data.get("description"),
        )
        self.db.add(sp)
        self.db.flush()
        return sp

    def update_sampling(
        self,
        sampling_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualitySamplingPlanModel:
        sp = self.get_sampling(sampling_id)
        for field in ("sampling_type", "fixed_count", "percentage", "minimum_count", "package_level", "lot_level", "custom_formula", "description"):
            if field in data and data[field] is not None:
                setattr(sp, field, data[field])
        self.db.flush()
        return sp

    def delete_sampling(self, sampling_id: UUID, principal: LogisticsPrincipal) -> None:
        sp = self.get_sampling(sampling_id)
        self.db.delete(sp)
        self.db.flush()
