from datetime import datetime, timezone

import pytest

from src.experiments.experiment_registry import ExperimentRegistry
from src.experiments.model_registry import ModelRegistry


def test_model_registry_does_not_overwrite_without_force(tmp_path) -> None:
    registry = ModelRegistry(tmp_path / "model_registry.json")
    record = {
        "model_family": "facial",
        "model_version": "facial-arcface-v0.1.0",
        "participant_id": None,
        "status": "candidate",
    }
    registry.register(record)
    with pytest.raises(FileExistsError):
        registry.register(record)
    registry.register({**record, "status": "rejected"}, force=True)
    assert registry.read()["models"][0]["status"] == "rejected"


def test_failed_experiment_is_not_marked_completed(tmp_path) -> None:
    registry = ExperimentRegistry(tmp_path / "experiments.parquet")
    record = {
        "experiment_id": "exp-1",
        "model_family": "pad",
        "status": "completed",
        "artifact_paths": [],
    }
    with pytest.raises(ValueError, match="artefactos"):
        registry.append(record)
    registry.append({**record, "status": "failed"})
    assert registry.read().iloc[0]["status"] == "failed"
