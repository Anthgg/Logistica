from __future__ import annotations

from typing import Any

from src.common.config import ArcFaceTrainingConfig


class InsightFaceUnavailable(RuntimeError):
    pass


def load_insightface(
    config: ArcFaceTrainingConfig,
    providers: list[str] | None = None,
) -> Any:
    try:
        from insightface.app import FaceAnalysis
    except ImportError as exc:
        raise InsightFaceUnavailable(
            "InsightFace no está instalado. Use Python 3.11 e instale requirements.txt."
        ) from exc
    selected_providers = providers or config.providers
    application = FaceAnalysis(name=config.model_name, providers=selected_providers)
    context_id = 0 if "CUDAExecutionProvider" in selected_providers else -1
    application.prepare(
        ctx_id=context_id,
        det_size=(config.detection_size.width, config.detection_size.height),
    )
    return application
