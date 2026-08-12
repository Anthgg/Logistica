import json
from pathlib import Path

import pandas as pd
from PIL import Image

from src.common.device import DeviceSelection
from src.common.hashing import sha256_file
from src.pipelines.train_facial_pipeline import run_facial_pipeline


def test_facial_dry_run_validates_without_writing_models(
    tmp_path, config, training_config
) -> None:
    data_root = config.pipeline.paths.root
    manifest_path = data_root / config.pipeline.facial_identity_manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, split in enumerate(("train", "validation"), start=1):
        image_path = data_root / f"face-{index}.jpg"
        Image.new("RGB", (16, 16), color=(index * 10, 0, 0)).save(image_path)
        rows.append(
            {
                "dataset_version": "pilot-v0.1.0",
                "protocol_version": "pilot-protocol-v0.1.0",
                "participant_id": "P-0001",
                "session_id": f"session-{split}",
                "capture_id": f"capture-{split}",
                "file_path": image_path.name,
                "checksum": sha256_file(image_path),
                "identity_label": "genuine",
                "sample_role": "enrollment" if split == "train" else "verification",
                "quality_status": "accepted",
                "split": split,
            }
        )
    pd.DataFrame(rows).to_parquet(manifest_path, index=False)
    frozen = tmp_path / "frozen_test_manifest.parquet"
    pd.DataFrame({"dataset": ["facial_identity"], "split": ["test"]}).to_parquet(
        frozen, index=False
    )
    checksum_path = tmp_path / "frozen_test_manifest.sha256"
    checksum_path.write_text(sha256_file(frozen) + "\n", encoding="utf-8")
    metadata_path = tmp_path / "frozen_test_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "dataset_version": "pilot-v0.1.0",
                "protocol_version": "pilot-protocol-v0.1.0",
            }
        ),
        encoding="utf-8",
    )
    models_root = tmp_path / "models"
    bundle = training_config.model_copy(
        update={
            "experiment": training_config.experiment.model_copy(
                update={
                    "models_root": str(models_root),
                    "reports_root": str(tmp_path / "reports"),
                    "registry_path": str(models_root / "registry" / "model_registry.json"),
                    "experiments_path": str(models_root / "registry" / "experiments.parquet"),
                    "frozen_test_manifest": str(frozen),
                    "frozen_test_checksum": str(checksum_path),
                    "frozen_test_metadata": str(metadata_path),
                }
            )
        }
    )
    result = run_facial_pipeline(
        config,
        bundle,
        device=DeviceSelection(
            requested="cpu",
            selected="cpu",
            tensorflow_gpus=(),
            onnx_providers=("CPUExecutionProvider",),
            message="test",
        ),
        output_dir=models_root,
        dry_run=True,
    )
    assert result.status == "validated"
    assert result.metrics["test_rows_used"] == 0
    assert not models_root.exists()
