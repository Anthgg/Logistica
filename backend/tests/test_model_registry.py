import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.ml.registry import sha256_file
from app.services.model_registry_service import ModelRegistryService


def _artifact(root: Path, name: str, content: bytes = b"fixture") -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name.replace("\\", "/"), "sha256": sha256_file(path)}


def _registry(
    root: Path,
    *,
    status: str = "candidate",
    checksum_override: str | None = None,
    test_rows_used: int = 0,
) -> Path:
    template = _artifact(root, "facial/P-0001.npz")
    threshold = _artifact(
        root,
        "facial/facial_threshold.json",
        (
            b'{"selected_threshold": 0.4,'
            b'"model_version": "facial-arcface-v0.1.0",'
            b'"dataset_version": "pilot-v0.1.0",'
            b'"test_rows_used": 0}'
        ),
    )
    if checksum_override:
        template["sha256"] = checksum_override
    path = root / "registry.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "models": [
                    {
                        "model_family": "facial",
                        "model_name": "buffalo_l",
                        "model_version": "facial-arcface-v0.1.0",
                        "dataset_version": "pilot-v0.1.0",
                        "protocol_version": "pilot-protocol-v0.1.0",
                        "status": status,
                        "artifacts": [template, threshold],
                        "test_rows_used": test_rows_used,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _service(root: Path, registry: Path) -> ModelRegistryService:
    configured = settings.model_copy(
        update={"FACIAL_MODEL_VERSION": "facial-arcface-v0.1.0"}
    )
    return ModelRegistryService(
        configured,
        registry_path=registry,
        artifact_root=root,
    )


def test_registry_loads_valid_candidate(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    snapshot = _service(tmp_path, registry).load()
    assert snapshot.checksum_valid is True
    assert snapshot.dataset_version == "pilot-v0.1.0"
    assert snapshot.models[0].record.status == "candidate"


@pytest.mark.parametrize(
    ("status", "test_rows"),
    [
        ("rejected", 0),
        ("failed", 0),
        ("incomplete", 0),
        ("candidate", 1),
    ],
)
def test_registry_rejects_disallowed_state_or_test_usage(
    tmp_path: Path, status: str, test_rows: int
) -> None:
    registry = _registry(
        tmp_path,
        status=status,
        test_rows_used=test_rows,
    )
    with pytest.raises(ApplicationError) as error:
        _service(tmp_path, registry).load()
    assert error.value.code == "MODEL_ARTIFACT_INVALID"


def test_registry_rejects_checksum_mismatch(tmp_path: Path) -> None:
    registry = _registry(tmp_path, checksum_override="0" * 64)
    with pytest.raises(ApplicationError) as error:
        _service(tmp_path, registry).load()
    assert error.value.code == "MODEL_ARTIFACT_INVALID"


def test_registry_rejects_missing_file(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    (tmp_path / "facial" / "P-0001.npz").unlink()
    with pytest.raises(ApplicationError) as error:
        _service(tmp_path, registry).load()
    assert error.value.code == "MODEL_ARTIFACT_INVALID"


def test_registry_rejects_invalid_json(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    registry.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ApplicationError) as error:
        _service(tmp_path, registry).load()
    assert error.value.code == "MODEL_REGISTRY_UNAVAILABLE"
