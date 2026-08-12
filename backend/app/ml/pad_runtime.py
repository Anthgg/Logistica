from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Protocol, cast

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import ApplicationError


class KerasPredictor(Protocol):
    @property
    def input_shape(self) -> object: ...

    def predict(self, values: object, *, verbose: int = 0) -> object: ...


@dataclass(frozen=True, slots=True)
class PadRawInference:
    attack_probability: float
    bona_fide_probability: float
    threshold: float
    decision: str
    latency_ms: float
    model_version: str
    image_decode_ms: float
    model_inference_ms: float


class PadRuntime:
    """La salida sigmoid del modelo representa probabilidad de ataque."""

    def __init__(
        self,
        *,
        model: KerasPredictor,
        model_version: str,
        threshold: float,
    ) -> None:
        self.model = model
        self.model_version = model_version
        self.threshold = threshold
        self._lock = RLock()
        self._numpy = self._import_numpy()
        self._height, self._width = self._input_dimensions(model.input_shape)

    @staticmethod
    def _import_numpy() -> object:
        try:
            import numpy
        except ImportError as exc:
            raise ApplicationError(
                "PAD_MODEL_UNAVAILABLE",
                "NumPy no está disponible para inferencia PAD.",
                503,
            ) from exc
        return numpy

    @staticmethod
    def load_model(path: Path) -> KerasPredictor:
        try:
            import tensorflow as tf
        except ImportError as exc:
            raise ApplicationError(
                "PAD_MODEL_UNAVAILABLE",
                "TensorFlow no está instalado.",
                503,
            ) from exc
        try:
            return cast(
                KerasPredictor,
                tf.keras.models.load_model(path, compile=False),
            )
        except Exception as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El modelo PAD registrado no es legible.",
                503,
            ) from exc

    @staticmethod
    def _input_dimensions(shape: object) -> tuple[int, int]:
        if not isinstance(shape, (tuple, list)) or len(shape) != 4:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El modelo PAD no tiene una entrada de imagen compatible.",
                503,
            )
        height, width = shape[1], shape[2]
        if not isinstance(height, int) or not isinstance(width, int):
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El tamaño de entrada PAD debe ser fijo.",
                503,
            )
        return height, width

    def infer(self, image_content: bytes) -> PadRawInference:
        started = perf_counter()
        try:
            with Image.open(BytesIO(image_content)) as source:
                image = source.convert("RGB").resize(
                    (self._width, self._height),
                    Image.Resampling.BILINEAR,
                )
                array = self._numpy.asarray(
                    image, dtype=self._numpy.float32
                )
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApplicationError(
                "INVALID_CAPTURE", "La captura PAD no es válida.", 422
            ) from exc
        decoded_at = perf_counter()
        batch = self._numpy.expand_dims(array, axis=0)
        with self._lock:
            prediction = self.model.predict(batch, verbose=0)
        inferred_at = perf_counter()
        values = self._numpy.asarray(prediction, dtype=float).reshape(-1)
        if (
            values.size != 1
            or not self._numpy.isfinite(values[0])
            or not 0 <= float(values[0]) <= 1
        ):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El modelo PAD devolvió una salida no válida.",
                500,
            )
        attack_probability = float(values[0])
        return PadRawInference(
            attack_probability=attack_probability,
            bona_fide_probability=1.0 - attack_probability,
            threshold=self.threshold,
            decision="attack"
            if attack_probability >= self.threshold
            else "bona_fide",
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model_version,
            image_decode_ms=(decoded_at - started) * 1000,
            model_inference_ms=(inferred_at - decoded_at) * 1000,
        )
