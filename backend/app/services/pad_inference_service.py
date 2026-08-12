from time import perf_counter

from app.core.exceptions import ApplicationError
from app.ml.model_bundle import ComponentInference
from app.services.model_loader_service import ModelLoaderService


class PadInferenceService:
    def __init__(self, loader: ModelLoaderService) -> None:
        self.loader = loader

    def infer(self, image_content: bytes) -> ComponentInference:
        runtime = self.loader.pad_runtime
        normalizer = self.loader.normalization
        if runtime is None:
            raise ApplicationError(
                "PAD_MODEL_UNAVAILABLE",
                "El modelo PAD no está disponible.",
                503,
            )
        if normalizer is None:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La normalización PAD no está disponible.",
                503,
            )
        result = runtime.infer(image_content)
        normalization_started = perf_counter()
        risk = normalizer.normalize("pad", result.attack_probability)
        normalization_ms = (
            perf_counter() - normalization_started
        ) * 1000
        return ComponentInference(
            available=True,
            valid=True,
            score=result.attack_probability,
            risk=risk,
            decision=result.decision,
            latency_ms=result.latency_ms,
            model_version=result.model_version,
            latency_breakdown={
                "image_decode_ms": result.image_decode_ms,
                "pad_ms": result.model_inference_ms,
                "normalization_ms": normalization_ms,
            },
        )
