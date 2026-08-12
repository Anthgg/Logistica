from pathlib import Path
from unittest.mock import Mock

from app.core.config import settings
from app.ml.behavioral_runtime import BehavioralRuntime
from app.ml.model_bundle import (
    ValidatedArtifact,
    ValidatedModelRecord,
)
from app.ml.registry import RegistryModelRecord
from app.services.model_loader_service import ModelLoaderService


def _behavioral_record(root: Path, participant: str) -> ValidatedModelRecord:
    names = (
        "autoencoder.keras",
        "scaler.joblib",
        "threshold.json",
        "feature_schema.json",
        "metadata.json",
    )
    artifacts = tuple(
        ValidatedArtifact(
            role=name,
            path=root / participant / name,
            checksum="0" * 64,
        )
        for name in names
    )
    record = RegistryModelRecord(
        model_family="behavioral",
        model_version=f"behavioral-ae-{participant}-v0.1.0",
        participant_id=participant,
        dataset_version="pilot-v0.1.0",
        protocol_version="pilot-protocol-v0.1.0",
        status="candidate",
        artifacts=[
            {
                "path": f"{participant}/{name}",
                "sha256": "0" * 64,
            }
            for name in names
        ],
    )
    return ValidatedModelRecord(record=record, artifacts=artifacts)


def test_missing_registry_starts_degraded(tmp_path: Path) -> None:
    configured = settings.model_copy(
        update={
            "MODEL_REGISTRY_PATH": str(tmp_path / "missing.json"),
            "REQUIRE_ALL_MODELS": False,
        }
    )
    loader = ModelLoaderService(configured)
    status = loader.startup()
    assert status.global_status == "unavailable"
    assert "MODEL_REGISTRY_UNAVAILABLE" in status.errors


def test_behavioral_lru_respects_cache_size(
    tmp_path: Path, monkeypatch
) -> None:
    configured = settings.model_copy(
        update={
            "BEHAVIORAL_MODEL_LOADING_MODE": "lru",
            "BEHAVIORAL_MODEL_CACHE_SIZE": 2,
        }
    )
    loader = ModelLoaderService(configured)
    loader._behavioral_records = {
        participant: _behavioral_record(tmp_path, participant)
        for participant in ("P-0001", "P-0002", "P-0003")
    }
    runtimes = {
        participant: Mock(spec=BehavioralRuntime)
        for participant in loader._behavioral_records
    }

    def fake_load(paths, *, model_version, dataset_version):
        del model_version, dataset_version
        participant = paths.model.parent.name
        return runtimes[participant]

    monkeypatch.setattr(
        BehavioralRuntime,
        "from_artifacts",
        staticmethod(fake_load),
    )
    loader.get_behavioral_runtime("P-0001")
    loader.get_behavioral_runtime("P-0002")
    loader.get_behavioral_runtime("P-0001")
    loader.get_behavioral_runtime("P-0003")
    assert list(loader._behavioral_cache) == ["P-0001", "P-0003"]
    assert loader.status.behavioral_loaded == 2


def test_behavioral_cache_loads_each_participant_once(
    tmp_path: Path, monkeypatch
) -> None:
    loader = ModelLoaderService(settings)
    loader._behavioral_records = {
        "P-0001": _behavioral_record(tmp_path, "P-0001")
    }
    runtime = Mock(spec=BehavioralRuntime)
    load = Mock(return_value=runtime)
    monkeypatch.setattr(
        BehavioralRuntime,
        "from_artifacts",
        staticmethod(load),
    )
    assert loader.get_behavioral_runtime("P-0001") is runtime
    assert loader.get_behavioral_runtime("P-0001") is runtime
    load.assert_called_once()
