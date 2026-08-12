import json
import subprocess
from pathlib import Path

import pandas as pd

from src.common.hashing import canonical_json_hash, sha256_file
from src.common.timestamps import iso_utc, utc_now


def git_commit(project_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build_dataset_metadata(
    *,
    dataset_version: str,
    protocol_version: str,
    config_values: dict[str, object],
    manifests: dict[str, pd.DataFrame],
    project_root: Path,
) -> dict[str, object]:
    scripts_root = project_root / "training" / "scripts"
    scripts = {
        path.relative_to(project_root).as_posix(): sha256_file(path)
        for path in sorted(scripts_root.glob("*.py"))
        if path.is_file()
    }
    counts = {
        name: {
            "rows": len(frame),
            "accepted": int(
                (frame.get("quality_status") == "accepted").sum()
                if "quality_status" in frame
                else len(frame)
            ),
            "rejected": int(
                (frame.get("quality_status") == "rejected").sum()
                if "quality_status" in frame
                else 0
            ),
        }
        for name, frame in manifests.items()
    }
    metadata: dict[str, object] = {
        "dataset_version": dataset_version,
        "protocol_version": protocol_version,
        "generated_at": iso_utc(utc_now()),
        "git_commit": git_commit(project_root),
        "configuration_hash": canonical_json_hash(config_values),
        "scripts": scripts,
        "datasets": counts,
    }
    metadata["metadata_hash"] = canonical_json_hash(metadata)
    return metadata


def write_dataset_metadata(metadata: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
