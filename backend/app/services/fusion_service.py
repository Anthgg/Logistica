import math
from time import perf_counter

from app.core.exceptions import ApplicationError
from app.ml.fusion_runtime import FusionConfig
from app.ml.model_bundle import FusedRisk


class FusionService:
    def __init__(self, config: FusionConfig) -> None:
        self.config = config

    def fuse(self, risks: dict[str, float | None]) -> FusedRisk:
        started = perf_counter()
        configured_weights = self.config.weights.model_dump()
        if any(
            value is not None
            and (not math.isfinite(value) or not 0 <= value <= 1)
            for value in risks.values()
        ):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "Un componente produjo un riesgo inválido.",
                500,
            )
        available = {
            name: value
            for name, value in risks.items()
            if value is not None and name in configured_weights
        }
        if len(available) < self.config.minimum_available_components:
            raise ApplicationError(
                "INSUFFICIENT_COMPONENTS",
                "No hay componentes biométricos suficientes para fusionar.",
                409,
            )
        strategy = self.config.missing_component_strategy
        missing = set(configured_weights) - set(available)
        if strategy == "reject" and missing:
            raise ApplicationError(
                "INSUFFICIENT_COMPONENTS",
                "La política exige todos los componentes biométricos.",
                409,
            )
        if strategy == "use_neutral_risk":
            if self.config.neutral_risk is None:
                raise ApplicationError(
                    "FUSION_CONFIG_UNAVAILABLE",
                    "La estrategia neutral no tiene riesgo configurado.",
                    503,
                )
            values = {
                name: available.get(name, self.config.neutral_risk)
                for name in configured_weights
            }
            combined = sum(
                configured_weights[name] * value
                for name, value in values.items()
            )
        else:
            selected_weights = {
                name: configured_weights[name] for name in available
            }
            weight_total = sum(selected_weights.values())
            if weight_total <= 0:
                raise ApplicationError(
                    "FUSION_CONFIG_UNAVAILABLE",
                    "Los pesos disponibles no permiten calcular el riesgo.",
                    503,
                )
            combined = sum(
                available[name] * selected_weights[name] / weight_total
                for name in available
            )
        return FusedRisk(
            risk=max(0.0, min(1.0, combined)),
            available_components=tuple(sorted(available)),
            strategy=strategy,
            latency_ms=(perf_counter() - started) * 1000,
        )
