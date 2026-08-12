from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import pandas as pd

from src.common.hashing import canonical_json_hash
from src.common.paths import PROJECT_ROOT

EXPERIMENT_COLUMNS = [
    "experiment_id",
    "experiment_name",
    "model_family",
    "model_name",
    "participant_id",
    "dataset_version",
    "protocol_version",
    "configuration_path",
    "configuration_checksum",
    "started_at",
    "finished_at",
    "duration_seconds",
    "status",
    "random_seed",
    "metrics",
    "artifact_paths",
    "artifact_checksums",
    "code_commit",
    "environment",
    "notes",
]


def create_experiment_id(model_family: str, name: str | None = None) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "".join(character for character in (name or model_family) if character.isalnum() or character in "-_")
    return f"{timestamp}-{safe_name[:40]}-{uuid4().hex[:8]}"


class ExperimentRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> pd.DataFrame:
        if not self.path.is_file():
            return pd.DataFrame(columns=EXPERIMENT_COLUMNS)
        return pd.read_parquet(self.path).reindex(columns=EXPERIMENT_COLUMNS)

    def append(self, record: dict[str, Any]) -> None:
        if record.get("status") == "completed":
            paths = [
                Path(value)
                if Path(value).is_absolute()
                else PROJECT_ROOT / Path(value)
                for value in record.get("artifact_paths", [])
            ]
            if not paths or any(not path.is_file() for path in paths):
                raise ValueError("No se puede completar un experimento con artefactos faltantes.")
        frame = self.read()
        if str(record["experiment_id"]) in set(frame["experiment_id"].astype(str)):
            raise ValueError("experiment_id ya existe.")
        normalized = {column: record.get(column) for column in EXPERIMENT_COLUMNS}
        for column in ("metrics", "artifact_paths", "artifact_checksums", "environment"):
            normalized[column] = json.dumps(
                normalized[column], ensure_ascii=False, sort_keys=True, default=str
            )
        updated = pd.concat([frame, pd.DataFrame([normalized])], ignore_index=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            suffix=".parquet", prefix=".experiments.", dir=self.path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        try:
            updated.to_parquet(temporary_path, index=False)
            os.replace(temporary_path, self.path)
        finally:
            temporary_path.unlink(missing_ok=True)


def finalize_experiment_record(
    *,
    experiment_id: str,
    experiment_name: str | None,
    model_family: str,
    model_name: str,
    participant_id: str | None,
    dataset_version: str,
    protocol_version: str,
    configuration_path: Path,
    configuration: dict[str, Any],
    started_at: datetime,
    status: str,
    random_seed: int,
    metrics: dict[str, Any] | None,
    artifacts: list[Path],
    environment: dict[str, Any],
    code_commit: str | None,
    notes: str | None = None,
) -> dict[str, Any]:
    finished = datetime.now(timezone.utc)
    from src.common.hashing import sha256_file

    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "model_family": model_family,
        "model_name": model_name,
        "participant_id": participant_id,
        "dataset_version": dataset_version,
        "protocol_version": protocol_version,
        "configuration_path": configuration_path.resolve().relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "configuration_checksum": canonical_json_hash(configuration),
        "started_at": started_at.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": (finished - started_at).total_seconds(),
        "status": status,
        "random_seed": random_seed,
        "metrics": metrics or {},
        "artifact_paths": [
            path.resolve().relative_to(PROJECT_ROOT).as_posix()
            for path in artifacts
        ],
        "artifact_checksums": {
            path.resolve().relative_to(PROJECT_ROOT).as_posix(): sha256_file(path)
            for path in artifacts
            if path.is_file()
        },
        "code_commit": code_commit,
        "environment": environment,
        "notes": notes,
    }
