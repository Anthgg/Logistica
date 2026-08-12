from dataclasses import dataclass
from pathlib import Path

from app.core.config import BACKEND_DIR, Settings
from app.core.exceptions import ApplicationError

PROJECT_ROOT = BACKEND_DIR.parent


def resolve_configured_path(value: str) -> Path:
    configured = Path(value)
    if not configured.is_absolute():
        configured = BACKEND_DIR / configured
    return configured.resolve()


def resolve_registry_artifact(value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ApplicationError(
            "MODEL_ARTIFACT_INVALID",
            "El registro contiene una ruta de artefacto no permitida.",
            503,
        )
    resolved = (PROJECT_ROOT / relative).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ApplicationError(
            "MODEL_ARTIFACT_INVALID",
            "El registro contiene una ruta fuera del proyecto.",
            503,
        ) from exc
    return resolved


@dataclass(frozen=True, slots=True)
class ResolvedModelSettings:
    registry_path: Path
    facial_templates_path: Path
    facial_threshold_path: Path
    insightface_model_root: Path
    pad_model_path: Path
    pad_threshold_path: Path
    behavioral_models_path: Path
    behavioral_features_path: Path
    fusion_config_path: Path
    normalization_config_path: Path

    @classmethod
    def from_settings(cls, source: Settings) -> "ResolvedModelSettings":
        return cls(
            registry_path=resolve_configured_path(source.MODEL_REGISTRY_PATH),
            facial_templates_path=resolve_configured_path(
                source.FACIAL_TEMPLATES_PATH
            ),
            facial_threshold_path=resolve_configured_path(
                source.FACIAL_THRESHOLD_PATH
            ),
            insightface_model_root=resolve_configured_path(
                source.INSIGHTFACE_MODEL_ROOT
            ),
            pad_model_path=resolve_configured_path(source.PAD_MODEL_PATH),
            pad_threshold_path=resolve_configured_path(
                source.PAD_THRESHOLD_PATH
            ),
            behavioral_models_path=resolve_configured_path(
                source.BEHAVIORAL_MODELS_PATH
            ),
            behavioral_features_path=resolve_configured_path(
                source.BEHAVIORAL_FEATURES_PATH
            ),
            fusion_config_path=resolve_configured_path(
                source.FUSION_CONFIG_PATH
            ),
            normalization_config_path=resolve_configured_path(
                source.NORMALIZATION_CONFIG_PATH
            ),
        )
