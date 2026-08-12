from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from src.common.hashing import canonical_json_hash, sha256_file


def write_json_atomic(path: str | Path, payload: Any) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2, default=str)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)
    return destination


def artifact_record(path: str | Path, root: str | Path) -> dict[str, str]:
    artifact = Path(path).resolve()
    base = Path(root).resolve()
    return {
        "path": artifact.relative_to(base).as_posix(),
        "sha256": sha256_file(artifact),
    }


def configuration_checksum(payload: Any) -> str:
    return canonical_json_hash(payload)
