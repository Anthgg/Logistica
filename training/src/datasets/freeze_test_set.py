import json
from pathlib import Path

import pandas as pd

from src.common.hashing import sha256_file
from src.common.timestamps import iso_utc, utc_now


class FrozenTestSetExistsError(FileExistsError):
    pass


def freeze_test_set(
    manifests: dict[str, pd.DataFrame],
    target: str | Path,
    *,
    dataset_version: str,
    protocol_version: str,
    force: bool = False,
    force_reason: str | None = None,
) -> tuple[Path, str, Path]:
    output = Path(target)
    hash_path = output.with_suffix(".sha256")
    metadata_path = output.with_name("frozen_test_metadata.json")
    if any(path.exists() for path in (output, hash_path, metadata_path)):
        if not force:
            raise FrozenTestSetExistsError(
                "El conjunto de prueba ya está congelado. Use --force con motivo."
            )
        if not force_reason or len(force_reason.strip()) < 5:
            raise ValueError("--force requiere un motivo explícito.")
    frames: list[pd.DataFrame] = []
    for dataset_name, frame in manifests.items():
        if frame.empty or "split" not in frame:
            continue
        selected = frame[frame["split"] == "test"].copy()
        selected.insert(0, "dataset", dataset_name)
        frames.append(selected)
    if not frames:
        raise ValueError("No existen registros de test para congelar.")
    frozen = pd.concat(frames, ignore_index=True, sort=False)
    sort_columns = [
        column
        for column in ("dataset", "participant_id", "session_id", "capture_id", "window_id")
        if column in frozen
    ]
    frozen = frozen.sort_values(sort_columns, kind="stable").reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    frozen.to_parquet(output, index=False)
    digest = sha256_file(output)
    hash_path.write_text(digest + "\n", encoding="utf-8")
    metadata = {
        "dataset_version": dataset_version,
        "protocol_version": protocol_version,
        "frozen_at": iso_utc(utc_now()),
        "frozen": True,
        "sha256": digest,
        "rows": len(frozen),
        "forced": force,
        "force_reason": force_reason if force else None,
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output, digest, metadata_path
