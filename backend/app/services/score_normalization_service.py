import math

from app.core.exceptions import ApplicationError
from app.ml.fusion_runtime import (
    ComponentNormalizationConfig,
    ScoreNormalizationConfig,
)


class ScoreNormalizationService:
    def __init__(self, config: ScoreNormalizationConfig) -> None:
        self.config = config

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, value))

    def normalize(self, component: str, score: float) -> float:
        if not math.isfinite(score):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El componente produjo un puntaje no finito.",
                500,
            )
        config = self.config.components.get(component)
        if not config:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "No existe normalización para un componente disponible.",
                503,
            )
        risk = self._apply(config, score)
        return self._clip(risk) if config.clipping else risk

    def _apply(
        self, config: ComponentNormalizationConfig, score: float
    ) -> float:
        if config.method == "logistic":
            slope = config.validation_statistics.get("logistic_slope")
            if slope is None or slope <= 0:
                raise ApplicationError(
                    "FUSION_CONFIG_UNAVAILABLE",
                    "La normalización logística está incompleta.",
                    503,
                )
            signed = score - config.threshold
            if config.risk_direction == "decreasing":
                signed = -signed
            return 1.0 / (1.0 + math.exp(-slope * signed))
        if config.method == "empirical_cdf":
            return self._empirical(config, score)
        if config.method == "piecewise_linear":
            return self._piecewise(config, score)
        ratio = (score - config.lower_bound) / (
            config.upper_bound - config.lower_bound
        )
        return ratio if config.risk_direction == "increasing" else 1.0 - ratio

    def _piecewise(
        self, config: ComponentNormalizationConfig, score: float
    ) -> float:
        if not config.lower_bound < config.threshold < config.upper_bound:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La normalización por tramos está incompleta.",
                503,
            )
        if score <= config.threshold:
            increasing = 0.5 * (score - config.lower_bound) / (
                config.threshold - config.lower_bound
            )
        else:
            increasing = 0.5 + 0.5 * (
                score - config.threshold
            ) / (config.upper_bound - config.threshold)
        return (
            increasing
            if config.risk_direction == "increasing"
            else 1.0 - increasing
        )

    def _empirical(
        self, config: ComponentNormalizationConfig, score: float
    ) -> float:
        points = sorted(
            (
                float(key.removeprefix("quantile_")),
                value,
            )
            for key, value in config.validation_statistics.items()
            if key.startswith("quantile_")
        )
        if len(points) < 2:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La CDF empírica no contiene cuantiles suficientes.",
                503,
            )
        if any(
            right_x <= left_x
            for (_, left_x), (_, right_x) in zip(points, points[1:])
        ):
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "Los cuantiles de la CDF empírica no son estrictamente crecientes.",
                503,
            )
        if score <= points[0][1]:
            probability = points[0][0]
        elif score >= points[-1][1]:
            probability = points[-1][0]
        else:
            probability = 0.0
            for (left_q, left_x), (right_q, right_x) in zip(
                points, points[1:]
            ):
                if left_x <= score <= right_x:
                    fraction = (score - left_x) / (right_x - left_x)
                    probability = left_q + fraction * (right_q - left_q)
                    break
        return (
            probability
            if config.risk_direction == "increasing"
            else 1.0 - probability
        )
