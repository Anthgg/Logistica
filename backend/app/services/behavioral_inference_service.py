from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import cast
from uuid import UUID

from app.core.exceptions import ApplicationError
from app.ml.model_bundle import ComponentInference
from app.services.model_loader_service import ModelLoaderService


class BehavioralFeatureStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def window(
        self,
        *,
        window_id: str,
        participant_code: str,
        experimental_session_id: UUID,
        feature_names: tuple[str, ...],
    ) -> dict[str, float]:
        if not self.path.is_file():
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "El almacén de ventanas conductuales no está disponible.",
                409,
            )
        try:
            import pandas
        except ImportError as exc:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "Pandas no está instalado para leer ventanas conductuales.",
                503,
            ) from exc
        try:
            with self._lock:
                frame = pandas.read_parquet(
                    self.path,
                    filters=[("window_id", "==", window_id)],
                    columns=[
                        "window_id",
                        "participant_id",
                        "experimental_session_id",
                        *feature_names,
                    ],
                )
        except Exception as exc:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "No fue posible leer el almacén conductual.",
                503,
            ) from exc
        if len(frame.index) != 1:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "La ventana conductual solicitada no está disponible.",
                409,
            )
        row = frame.iloc[0]
        if (
            str(row["participant_id"]) != participant_code
            or str(row["experimental_session_id"])
            != str(experimental_session_id)
        ):
            raise ApplicationError(
                "RESEARCH_RESOURCE_FORBIDDEN",
                "La ventana no corresponde a la sesión autenticada.",
                403,
            )
        return {
            name: float(cast(object, row[name])) for name in feature_names
        }


class BehavioralInferenceService:
    def __init__(
        self,
        loader: ModelLoaderService,
        feature_store: BehavioralFeatureStore | None = None,
    ) -> None:
        self.loader = loader
        self.feature_store = feature_store or BehavioralFeatureStore(
            loader.paths.behavioral_features_path
        )

    def infer(
        self,
        *,
        participant_code: str,
        window_id: str,
        experimental_session_id: UUID,
    ) -> ComponentInference:
        normalizer = self.loader.normalization
        if normalizer is None:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La normalización conductual no está disponible.",
                503,
            )
        load_started = perf_counter()
        runtime = self.loader.get_behavioral_runtime(participant_code)
        behavioral_load_ms = (perf_counter() - load_started) * 1000
        values = self.feature_store.window(
            window_id=window_id,
            participant_code=participant_code,
            experimental_session_id=experimental_session_id,
            feature_names=runtime.feature_names,
        )
        result = runtime.infer(values)
        normalization_started = perf_counter()
        risk = normalizer.normalize(
            "behavioral", result.reconstruction_error
        )
        normalization_ms = (
            perf_counter() - normalization_started
        ) * 1000
        return ComponentInference(
            available=True,
            valid=True,
            score=result.reconstruction_error,
            risk=risk,
            decision=result.decision,
            latency_ms=result.latency_ms,
            model_version=result.model_version,
            latency_breakdown={
                "behavioral_load_ms": behavioral_load_ms,
                "behavioral_ms": result.latency_ms,
                "normalization_ms": normalization_ms,
            },
        )
