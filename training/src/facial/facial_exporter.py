from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.common.hashing import sha256_file
from src.common.paths import PROJECT_ROOT
from src.common.serialization import write_json_atomic


def export_facial_metadata(
    destination: Path,
    *,
    model_version: str,
    dataset_version: str,
    template_paths: Iterable[Path],
    threshold_path: Path,
    metrics_path: Path,
) -> Path:
    artifacts = [*template_paths, threshold_path, metrics_path]
    missing = [path for path in artifacts if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Faltan artefactos faciales: " + ", ".join(path.name for path in missing)
        )
    return write_json_atomic(
        destination,
        {
            "model_type": "arcface_verification",
            "model_version": model_version,
            "dataset_version": dataset_version,
            "status": "candidate",
            "test_rows_used": 0,
            "artifacts": [
                {
                    "path": path.resolve().relative_to(PROJECT_ROOT).as_posix(),
                    "sha256": sha256_file(path),
                }
                for path in artifacts
            ],
        },
    )
