from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NormalizationMethod = Literal[
    "min_max_robust",
    "logistic",
    "piecewise_linear",
    "empirical_cdf",
]
MissingComponentStrategy = Literal[
    "reject",
    "renormalize_available_weights",
    "use_neutral_risk",
    "require_minimum_components",
]


class ComponentNormalizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    lower_bound: float
    upper_bound: float
    threshold: float
    clipping: bool = True
    risk_direction: Literal["increasing", "decreasing"]
    dataset_version: str
    validation_statistics: dict[str, float]

    @model_validator(mode="after")
    def validate_bounds(self) -> "ComponentNormalizationConfig":
        if self.lower_bound >= self.upper_bound:
            raise ValueError("lower_bound debe ser menor que upper_bound.")
        return self


class ScoreNormalizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalization_version: str
    components: dict[str, ComponentNormalizationConfig]
    dataset_version: str
    generated_at: datetime
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")


class FusionWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facial: float = Field(ge=0, le=1)
    pad: float = Field(ge=0, le=1)
    behavioral: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_sum(self) -> "FusionWeights":
        if abs(self.facial + self.pad + self.behavioral - 1.0) > 1e-9:
            raise ValueError("Los pesos de fusión deben sumar 1.")
        return self


class RiskThresholdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    low_max: float = Field(ge=0, le=1)
    medium_max: float = Field(ge=0, le=1)
    high_max: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_order(self) -> "RiskThresholdConfig":
        if not self.low_max < self.medium_max < self.high_max < 1:
            raise ValueError("Los límites de riesgo deben ser crecientes.")
        return self


class FusionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fusion_version: str
    method: Literal["weighted_late_fusion"]
    weights: FusionWeights
    missing_component_strategy: MissingComponentStrategy
    minimum_available_components: int = Field(default=2, ge=1, le=3)
    neutral_risk: float | None = Field(default=None, ge=0, le=1)
    risk_thresholds: RiskThresholdConfig
    validation_metrics: dict[str, float]
    dataset_version: str
    generated_at: datetime
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
