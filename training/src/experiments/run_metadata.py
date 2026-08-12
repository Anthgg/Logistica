from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.reproducibility import environment_metadata


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_metadata(
    *,
    project_root: Path,
    dataset_version: str,
    protocol_version: str,
    configuration: dict[str, Any],
    device: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_version": dataset_version,
        "protocol_version": protocol_version,
        "configuration": configuration,
        "device": device,
        "environment": environment_metadata(project_root),
        "recorded_at": utc_now_iso(),
        "test_rows_used": 0,
    }
