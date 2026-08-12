from pathlib import Path

import pandas as pd
import pytest

from src.behavioral.behavioral_manifest import build_behavioral_manifest
from src.datasets.freeze_test_set import (
    FrozenTestSetExistsError,
    freeze_test_set,
)
from src.datasets.manifest_builder import write_manifest


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_version": "pilot-v0.1.0",
                "protocol_version": "protocol",
                "generated_at": "2026-01-01T00:00:00Z",
                "source_session_id": "session",
                "participant_id": "participant",
                "session_id": "session",
                "window_id": "window",
                "checksum": "abc",
                "quality_status": "accepted",
                "rejection_reasons": [],
                "split": "test",
                "dwell_mean": 100.0,
            }
        ]
    )


def test_features_do_not_contain_key():
    assert "key" not in build_behavioral_manifest(_features()).columns


def test_features_do_not_contain_code():
    assert "code" not in build_behavioral_manifest(_features()).columns


def test_manifest_contains_checksums():
    manifest = build_behavioral_manifest(_features())
    assert manifest.loc[0, "checksum"] == "abc"


def test_absolute_paths_are_rejected(tmp_path):
    frame = _features()
    frame["file_path"] = str((tmp_path / "face.jpg").resolve())
    with pytest.raises(ValueError):
        write_manifest(frame, tmp_path / "manifest.parquet")


def test_frozen_test_is_not_replaced(tmp_path):
    target = tmp_path / "frozen_test_manifest.parquet"
    freeze_test_set(
        {"behavioral": _features()},
        target,
        dataset_version="pilot-v0.1.0",
        protocol_version="protocol",
    )
    with pytest.raises(FrozenTestSetExistsError):
        freeze_test_set(
            {"behavioral": _features()},
            target,
            dataset_version="pilot-v0.1.0",
            protocol_version="protocol",
        )


def test_force_allows_controlled_replacement(tmp_path):
    target = tmp_path / "frozen_test_manifest.parquet"
    arguments = {
        "manifests": {"behavioral": _features()},
        "target": target,
        "dataset_version": "pilot-v0.1.0",
        "protocol_version": "protocol",
    }
    freeze_test_set(**arguments)
    freeze_test_set(
        **arguments,
        force=True,
        force_reason="Corrección documentada del protocolo",
    )
    assert target.is_file()
