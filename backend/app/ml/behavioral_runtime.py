import json
import math
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

from app.core.exceptions import ApplicationError
from app.ml.registry import canonical_checksum


class Scaler(Protocol):
    def transform(self, values: object) -> object: ...


class Autoencoder(Protocol):
    @property
    def input_shape(self) -> object: ...

    def predict(self, values: object, *, verbose: int = 0) -> object: ...


class FeatureDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    position: int = Field(ge=0)
    dtype: Literal["float32", "float64"]
    allowed: Literal["finite"]


class FeatureSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: str
    dataset_version: str
    feature_count: int = Field(gt=0)
    features: list[FeatureDefinition]
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    def ordered_names(self) -> tuple[str, ...]:
        ordered = sorted(self.features, key=lambda item: item.position)
        names = tuple(item.name for item in ordered)
        positions = tuple(item.position for item in ordered)
        if positions != tuple(range(len(ordered))):
            raise ValueError("Las posiciones del esquema no son consecutivas.")
        if len(names) != self.feature_count or len(set(names)) != len(names):
            raise ValueError("El esquema de características es inconsistente.")
        return names


@dataclass(frozen=True, slots=True)
class BehavioralArtifactPaths:
    model: Path
    scaler: Path
    threshold: Path
    feature_schema: Path
    metadata: Path


@dataclass(frozen=True, slots=True)
class BehavioralRawInference:
    reconstruction_error: float
    threshold: float
    decision: str
    latency_ms: float
    model_version: str


class BehavioralRuntime:
    def __init__(
        self,
        *,
        model: Autoencoder,
        scaler: Scaler,
        schema: FeatureSchema,
        threshold: float,
        model_version: str,
    ) -> None:
        self.model = model
        self.scaler = scaler
        self.schema = schema
        self.threshold = threshold
        self.model_version = model_version
        self.feature_names = schema.ordered_names()
        self._lock = RLock()
        self._numpy = self._import_numpy()
        self._validate_model_dimension()

    @staticmethod
    def _import_numpy() -> object:
        try:
            import numpy
        except ImportError as exc:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "NumPy no está disponible para inferencia conductual.",
                503,
            ) from exc
        return numpy

    @classmethod
    def from_artifacts(
        cls,
        paths: BehavioralArtifactPaths,
        *,
        model_version: str,
        dataset_version: str,
    ) -> "BehavioralRuntime":
        try:
            import joblib
            import tensorflow as tf
        except ImportError as exc:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "Las dependencias del modelo conductual no están instaladas.",
                503,
            ) from exc
        try:
            model = cast(
                Autoencoder,
                tf.keras.models.load_model(paths.model, compile=False),
            )
            scaler = cast(Scaler, joblib.load(paths.scaler))
            schema_payload = json.loads(
                paths.feature_schema.read_text(encoding="utf-8")
            )
            if not isinstance(schema_payload, dict):
                raise ValueError("feature schema root")
            typed_schema_payload = cast(
                dict[str, object], schema_payload
            )
            if typed_schema_payload.get("checksum") != canonical_checksum(
                typed_schema_payload
            ):
                raise ValueError("feature schema checksum")
            schema = FeatureSchema.model_validate(typed_schema_payload)
            threshold_payload = json.loads(
                paths.threshold.read_text(encoding="utf-8")
            )
            metadata_payload = json.loads(
                paths.metadata.read_text(encoding="utf-8")
            )
            if (
                not isinstance(threshold_payload, dict)
                or not isinstance(metadata_payload, dict)
            ):
                raise ValueError("behavioral metadata root")
            threshold = float(threshold_payload["threshold"])
        except Exception as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El bundle conductual registrado no es legible.",
                503,
            ) from exc
        if (
            schema.dataset_version != dataset_version
            or threshold_payload.get("dataset_version") != dataset_version
            or metadata_payload.get("dataset_version") != dataset_version
            or threshold_payload.get("model_version") != model_version
            or metadata_payload.get("model_version") != model_version
        ):
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El bundle conductual mezcla versiones incompatibles.",
                503,
            )
        if not math.isfinite(threshold) or threshold < 0:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El umbral conductual registrado no es válido.",
                503,
            )
        return cls(
            model=model,
            scaler=scaler,
            schema=schema,
            threshold=threshold,
            model_version=model_version,
        )

    def _validate_model_dimension(self) -> None:
        shape = self.model.input_shape
        scaler_features = getattr(self.scaler, "n_features_in_", None)
        if (
            not isinstance(shape, (tuple, list))
            or len(shape) != 2
            or shape[1] != len(self.feature_names)
            or (
                scaler_features is not None
                and scaler_features != len(self.feature_names)
            )
        ):
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El Autoencoder y el esquema conductual son incompatibles.",
                503,
            )

    def infer(
        self, feature_values: dict[str, float]
    ) -> BehavioralRawInference:
        started = perf_counter()
        if set(feature_values) != set(self.feature_names):
            raise ApplicationError(
                "FEATURE_SCHEMA_MISMATCH",
                "La ventana no coincide con el esquema del participante.",
                422,
            )
        ordered = [feature_values[name] for name in self.feature_names]
        if not all(math.isfinite(value) for value in ordered):
            raise ApplicationError(
                "FEATURE_SCHEMA_MISMATCH",
                "La ventana contiene valores no finitos.",
                422,
            )
        matrix = self._numpy.asarray([ordered], dtype=self._numpy.float64)
        try:
            scaled = self.scaler.transform(matrix)
        except (TypeError, ValueError) as exc:
            raise ApplicationError(
                "FEATURE_SCHEMA_MISMATCH",
                "El scaler rechazó la ventana conductual.",
                422,
            ) from exc
        with self._lock:
            reconstructed = self.model.predict(scaled, verbose=0)
        output = self._numpy.asarray(reconstructed, dtype=float)
        if output.shape != self._numpy.asarray(scaled).shape:
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El Autoencoder devolvió una forma incompatible.",
                500,
            )
        error = float(self._numpy.mean(self._numpy.square(scaled - output)))
        if not math.isfinite(error):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El Autoencoder devolvió un error no finito.",
                500,
            )
        return BehavioralRawInference(
            reconstruction_error=error,
            threshold=self.threshold,
            decision="legitimate"
            if error <= self.threshold
            else "anomalous",
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model_version,
        )
