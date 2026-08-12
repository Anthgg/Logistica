from time import perf_counter

from app.core.exceptions import ApplicationError
from app.ml.model_bundle import ComponentInference
from app.services.model_loader_service import ModelLoaderService


class FacialInferenceService:
    def __init__(self, loader: ModelLoaderService) -> None:
        self.loader = loader

    def infer(
        self, participant_code: str, image_content: bytes
    ) -> ComponentInference:
        runtime = self.loader.facial_runtime
        normalizer = self.loader.normalization
        if runtime is None:
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "El modelo facial no está disponible.",
                503,
            )
        if normalizer is None:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La normalización facial no está disponible.",
                503,
            )
        result = runtime.infer(participant_code, image_content)
        normalization_started = perf_counter()
        risk = normalizer.normalize("facial", result.similarity)
        normalization_ms = (
            perf_counter() - normalization_started
        ) * 1000
        return ComponentInference(
            available=True,
            valid=True,
            score=result.similarity,
            risk=risk,
            decision=result.decision,
            latency_ms=result.latency_ms,
            model_version=result.model_version,
            latency_breakdown={
                "image_decode_ms": result.image_decode_ms,
                "facial_ms": result.model_inference_ms,
                "normalization_ms": normalization_ms,
            },
        )
