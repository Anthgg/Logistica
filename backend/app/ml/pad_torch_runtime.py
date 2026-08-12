"""Runtime PAD con PyTorch MobileNetV2 para el experimento PAD-A.

Carga el checkpoint ``pad_a_mobilenetv2.pt`` entrenado con CelebA-Spoof
y expone inferencia de probabilidad de ataque para imágenes subidas.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import RLock
from time import perf_counter

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PadTorchInference:
    attack_probability: float
    bona_fide_probability: float
    threshold: float
    decision: str
    latency_ms: float
    model_version: str
    image_decode_ms: float
    model_inference_ms: float
    framework: str


class PadTorchRuntime:
    """Runtime de inferencia PAD usando MobileNetV2 de torchvision."""

    def __init__(
        self,
        *,
        model_path: Path,
        model_version: str,
        threshold: float,
        image_size: int = 224,
    ) -> None:
        self.model_path = Path(model_path)
        self.model_version = model_version
        self.threshold = threshold
        self.image_size = image_size
        self._lock = RLock()
        self._model = self._load_model()
        self._device = self._resolve_device()
        self._transform = self._build_transform()

    def _load_model(self) -> object:
        try:
            import torch
            from torchvision import transforms  # noqa: F401
            from torchvision.models import mobilenet_v2
        except ImportError as exc:
            raise ApplicationError(
                "PAD_MODEL_UNAVAILABLE",
                "PyTorch no está instalado para inferencia PAD.",
                503,
            ) from exc

        try:
            import torch.nn as nn
            backbone = mobilenet_v2(weights=None)
            features = backbone.classifier[1].in_features
            backbone.classifier = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(features, 128),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.2),
                nn.Linear(128, 1),
            )
            state_dict = torch.load(
                self.model_path, map_location="cpu", weights_only=True
            )
            backbone.load_state_dict(state_dict)
            backbone.eval()
            logger.info("PAD-A MobileNetV2 cargado desde %s", self.model_path)
            return backbone
        except Exception as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                f"El modelo PAD-A no es legible: {exc}",
                503,
            ) from exc

    @staticmethod
    def _resolve_device() -> str:
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _build_transform(self) -> object:
        from torchvision import transforms
        return transforms.Compose(
            [
                transforms.Resize((self.image_size, self.image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def infer(self, image_content: bytes) -> PadTorchInference:
        import torch
        started = perf_counter()
        try:
            with Image.open(BytesIO(image_content)) as source:
                image = source.convert("RGB")
                tensor = self._transform(image).unsqueeze(0).to(self._device)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApplicationError(
                "INVALID_CAPTURE", "La captura PAD no es válida.", 422
            ) from exc
        decoded_at = perf_counter()
        with self._lock:
            with torch.no_grad():
                logits = self._model(tensor)
                probability = torch.sigmoid(logits).cpu().numpy().flatten()[0]
        inferred_at = perf_counter()
        if not (0.0 <= float(probability) <= 1.0):
            raise ApplicationError(
                "INTERNAL_INFERENCE_ERROR",
                "El modelo PAD devolvió una salida no válida.",
                500,
            )
        attack_probability = float(probability)
        return PadTorchInference(
            attack_probability=attack_probability,
            bona_fide_probability=1.0 - attack_probability,
            threshold=self.threshold,
            decision="attack" if attack_probability >= self.threshold else "bona_fide",
            latency_ms=(perf_counter() - started) * 1000,
            model_version=self.model_version,
            image_decode_ms=(decoded_at - started) * 1000,
            model_inference_ms=(inferred_at - decoded_at) * 1000,
            framework="pytorch",
        )


_runtime: PadTorchRuntime | None = None
_runtime_lock = RLock()


def get_pad_torch_runtime() -> PadTorchRuntime | None:
    global _runtime
    if _runtime is not None:
        return _runtime
    with _runtime_lock:
        if _runtime is not None:
            return _runtime
        model_path = Path("/app/models/pad_a_mobilenetv2.pt")
        metrics_path = Path("/app/models/pad_a_metrics.json")
        if not model_path.is_file():
            logger.info("PAD-A model no encontrado en %s; runtime deshabilitado.", model_path)
            return None
        threshold = 0.5
        model_version = "pad-a-v0.1.0"
        if metrics_path.is_file():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                threshold = float(metrics.get("threshold", 0.5))
                model_version = str(metrics.get("model_version", model_version))
            except (json.JSONDecodeError, ValueError):
                pass
        _runtime = PadTorchRuntime(
            model_path=model_path,
            model_version=model_version,
            threshold=threshold,
        )
        return _runtime