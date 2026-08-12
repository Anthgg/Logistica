from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


DeviceRequest = Literal["auto", "cpu", "gpu"]


@dataclass(frozen=True)
class DeviceSelection:
    requested: DeviceRequest
    selected: Literal["cpu", "gpu"]
    tensorflow_gpus: tuple[str, ...]
    onnx_providers: tuple[str, ...]
    message: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _tensorflow_gpus() -> tuple[str, ...]:
    try:
        import tensorflow as tf

        return tuple(device.name for device in tf.config.list_physical_devices("GPU"))
    except (ImportError, RuntimeError):
        return ()


def _onnx_providers() -> tuple[str, ...]:
    try:
        import onnxruntime as ort

        return tuple(ort.get_available_providers())
    except ImportError:
        return ()


def select_device(requested: DeviceRequest = "auto") -> DeviceSelection:
    if requested not in {"auto", "cpu", "gpu"}:
        raise ValueError("--device debe ser auto, cpu o gpu.")
    tensorflow_gpus = _tensorflow_gpus()
    onnx_providers = _onnx_providers()
    gpu_available = bool(tensorflow_gpus) and "CUDAExecutionProvider" in onnx_providers
    if requested == "cpu":
        selected = "cpu"
        message = "CPU seleccionada explícitamente."
    elif requested == "gpu" and gpu_available:
        selected = "gpu"
        message = "GPU compatible detectada para TensorFlow y ONNX Runtime."
    elif requested == "gpu":
        selected = "cpu"
        message = "GPU solicitada pero no compatible; se utilizará CPU de forma segura."
    elif gpu_available:
        selected = "gpu"
        message = "GPU compatible seleccionada automáticamente."
    else:
        selected = "cpu"
        message = "No se detectó una GPU compatible; se utilizará CPU."
    return DeviceSelection(
        requested=requested,
        selected=selected,
        tensorflow_gpus=tensorflow_gpus,
        onnx_providers=onnx_providers,
        message=message,
    )


def insightface_providers(selection: DeviceSelection) -> list[str]:
    if selection.selected == "gpu":
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]
