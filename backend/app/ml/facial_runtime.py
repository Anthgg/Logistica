from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Protocol, cast

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import ApplicationError


class DetectedFace(Protocol):
    @property
    def normed_embedding(self) -> object: ...


class FaceAnalyzer(Protocol):
    def prepare(self, *, ctx_id: int, det_size: tuple[int, int]) -> None: ...

    def get(self, image: object) -> list[DetectedFace]: ...


@dataclass(frozen=True, slots=True)
class FacialRawInference:
    similarity: float
    threshold: float
    decision: str
    latency_ms: float
    model_version: str
    image_decode_ms: float
    model_inference_ms: float


class FacialRuntime:
    def __init__(
        self,
        *,
        model_name: str,
        model_version: str,
        model_root: Path,
        templates_path: Path | None,
        threshold: float,
        device: str,
        analyzer: FaceAnalyzer | None = None,
        template_paths: tuple[Path, ...] = (),
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.threshold = threshold
        self._lock = RLock()
        self._numpy = self._import_numpy()
        selected_templates = template_paths
        if not selected_templates and templates_path is not None:
            selected_templates = tuple(
                sorted(templates_path.glob("*.npz"))
            )
        self._templates = self._load_templates(selected_templates)
        self._analyzer = analyzer or self._create_analyzer(
            model_name=model_name,
            model_root=model_root,
            device=device,
        )

    @staticmethod
    def _import_numpy() -> object:
        try:
            import numpy
        except ImportError as exc:
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "NumPy no está disponible para inferencia facial.",
                503,
            ) from exc
        return numpy

    def _create_analyzer(
        self, *, model_name: str, model_root: Path, device: str
    ) -> FaceAnalyzer:
        local_model = model_root / "models" / model_name
        if not local_model.is_dir():
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "El paquete local de InsightFace no está disponible.",
                503,
            )
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "InsightFace no está instalado.",
                503,
            ) from exc
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device == "gpu"
            else ["CPUExecutionProvider"]
        )
        try:
            analyzer = cast(
                FaceAnalyzer,
                FaceAnalysis(
                    name=model_name,
                    root=str(model_root),
                    providers=providers,
                    allowed_modules=["detection", "recognition"],
                ),
            )
            analyzer.prepare(
                ctx_id=0 if device == "gpu" else -1,
                det_size=(640, 640),
            )
        except Exception as exc:
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "El runtime local de InsightFace no pudo inicializarse.",
                503,
            ) from exc
        return analyzer

    def _normalize(self, vector: object) -> object:
        numpy = self._numpy
        array = numpy.asarray(vector, dtype=numpy.float32)
        if (
            array.ndim != 1
            or array.size == 0
            or not numpy.isfinite(array).all()
        ):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El descriptor facial no es un vector finito.",
                500,
            )
        norm = float(numpy.linalg.norm(array))
        if not norm or not numpy.isfinite(norm):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "No fue posible normalizar el descriptor facial.",
                500,
            )
        return array / norm

    def _load_templates(
        self, paths: tuple[Path, ...]
    ) -> dict[str, object]:
        templates: dict[str, object] = {}
        for path in paths:
            if path.stem in templates:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Existen plantillas duplicadas para un participante.",
                    503,
                )
            try:
                with self._numpy.load(path, allow_pickle=False) as content:
                    templates[path.stem] = self._normalize(
                        content["template"]
                    )
            except ApplicationError as exc:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Una plantilla facial registrada no es válida.",
                    503,
                ) from exc
            except (KeyError, OSError, ValueError) as exc:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Una plantilla facial registrada no es válida.",
                    503,
                ) from exc
        if not templates:
            raise ApplicationError(
                "FACIAL_MODEL_UNAVAILABLE",
                "No existen plantillas faciales registradas y cargables.",
                503,
            )
        return templates

    def infer(
        self, participant_code: str, image_content: bytes
    ) -> FacialRawInference:
        template = self._templates.get(participant_code)
        if template is None:
            raise ApplicationError(
                "FACIAL_TEMPLATE_NOT_FOUND",
                "No existe una plantilla facial para el participante.",
                409,
            )
        started = perf_counter()
        try:
            with Image.open(BytesIO(image_content)) as source:
                rgb = self._numpy.asarray(
                    source.convert("RGB"), dtype=self._numpy.uint8
                )
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApplicationError(
                "INVALID_CAPTURE", "La captura facial no es válida.", 422
            ) from exc
        decoded_at = perf_counter()
        bgr = rgb[:, :, ::-1]
        with self._lock:
            faces = self._analyzer.get(bgr)
        inferred_at = perf_counter()
        if not faces:
            raise ApplicationError(
                "NO_FACE_DETECTED", "No se detectó un rostro.", 422
            )
        if len(faces) != 1:
            raise ApplicationError(
                "MULTIPLE_FACES_DETECTED",
                "Se detectó más de un rostro.",
                422,
            )
        embedding = self._normalize(faces[0].normed_embedding)
        if embedding.shape != template.shape:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "La plantilla y el descriptor facial son incompatibles.",
                503,
            )
        similarity = float(self._numpy.dot(embedding, template))
        similarity = max(-1.0, min(1.0, similarity))
        return FacialRawInference(
            similarity=similarity,
            threshold=self.threshold,
            decision="genuine"
            if similarity >= self.threshold
            else "impostor",
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model_version,
            image_decode_ms=(decoded_at - started) * 1000,
            model_inference_ms=(inferred_at - decoded_at) * 1000,
        )
