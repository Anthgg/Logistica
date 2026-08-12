import argparse
import json

from _training import load_bundles
from src.common.hashing import sha256_file
from src.common.paths import PROJECT_ROOT
from src.experiments.model_registry import ModelRegistry
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Registra modelos candidatos cuyos artefactos ya fueron verificados."
    )
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    _, bundle = load_bundles(arguments.config_dir, arguments.dataset_version, None)
    paths = training_paths(bundle)
    registry = ModelRegistry(paths.registry_path)
    metadata_paths = [
        *sorted((paths.models_root / "facial" / "metadata").glob("*/*.json")),
        *sorted((paths.models_root / "pad" / "metadata").glob("*.json")),
        *sorted(
            (paths.models_root / "behavioral" / "participants").glob(
                "*/*/metadata.json"
            )
        ),
    ]
    registered = 0
    for path in metadata_paths:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("status") != "candidate":
            continue
        artifacts = [
            item
            for item in path.parent.iterdir()
            if item.is_file() and item.name != "metadata.json"
        ]
        registry.register(
            {
                "model_family": metadata.get("model_type"),
                "model_name": metadata.get("model_name", metadata.get("model_type")),
                "model_version": metadata["model_version"],
                "participant_id": metadata.get("participant_id"),
                "dataset_version": metadata["dataset_version"],
                "protocol_version": metadata.get(
                    "protocol_version", bundle.experiment.protocol_version
                ),
                "status": "candidate",
                "artifacts": [
                    {
                        "path": item.resolve().relative_to(PROJECT_ROOT).as_posix(),
                        "sha256": sha256_file(item),
                    }
                    for item in artifacts
                ],
                "test_rows_used": 0,
            },
            force=arguments.force,
        )
        registered += 1
    print(f"Modelos registrados: {registered}")


if __name__ == "__main__":
    main()
