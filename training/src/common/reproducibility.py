from __future__ import annotations

import os
import platform
import random
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np


def configure_reproducibility(seed: int, deterministic_operations: bool = True) -> dict[str, Any]:
    os.environ["PYTHONHASHSEED"] = str(seed)
    if deterministic_operations:
        os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
    random.seed(seed)
    np.random.seed(seed)
    tensorflow_configured = False
    warning: str | None = None
    try:
        import tensorflow as tf

        tf.keras.utils.set_random_seed(seed)
        if deterministic_operations:
            try:
                tf.config.experimental.enable_op_determinism()
            except (AttributeError, RuntimeError) as exc:
                warning = str(exc)
        tensorflow_configured = True
    except ImportError:
        warning = "TensorFlow no está instalado; se configuraron random y NumPy."
    return {
        "random_seed": seed,
        "tensorflow_configured": tensorflow_configured,
        "deterministic_operations_requested": deterministic_operations,
        "determinism_warning": warning,
        "claim": (
            "Las semillas y operaciones deterministas disponibles fueron configuradas; "
            "el determinismo absoluto no se garantiza en todas las combinaciones GPU/CUDA."
        ),
    }


def _version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _git_commit(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def environment_metadata(project_root: Path) -> dict[str, Any]:
    memory_bytes: int | None = None
    try:
        import psutil

        memory_bytes = int(psutil.virtual_memory().available)
    except ImportError:
        pass
    cuda_built = False
    cudnn_version: str | None = None
    try:
        import tensorflow as tf

        build = tf.sysconfig.get_build_info()
        cuda_built = bool(tf.test.is_built_with_cuda())
        cudnn_version = str(build.get("cudnn_version") or "") or None
    except ImportError:
        pass
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "operating_system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "available_ram_bytes": memory_bytes,
        "tensorflow": _version("tensorflow"),
        "cuda_built": cuda_built,
        "cudnn": cudnn_version,
        "insightface": _version("insightface"),
        "onnxruntime": _version("onnxruntime") or _version("onnxruntime-gpu"),
        "numpy": _version("numpy"),
        "scikit_learn": _version("scikit-learn"),
        "git_commit": _git_commit(project_root),
    }
