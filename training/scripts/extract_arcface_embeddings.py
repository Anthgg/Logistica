import argparse
from pathlib import Path

import pandas as pd

from _training import add_common_training_arguments, load_bundles
from src.common.device import insightface_providers, select_device
from src.common.validation import validate_training_inputs
from src.facial.embedding_extractor import extract_embeddings, save_embeddings
from src.facial.insightface_loader import load_insightface
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae embeddings ArcFace de train/validation.")
    add_common_training_arguments(parser)
    arguments = parser.parse_args()
    preparation, bundle = load_bundles(
        arguments.config_dir, arguments.dataset_version, arguments.random_seed
    )
    validate_training_inputs(preparation, bundle).raise_if_invalid()
    config = bundle.arcface
    manifest = pd.read_parquet(
        preparation.pipeline.paths.root
        / preparation.pipeline.facial_identity_manifest
    )
    destination = (
        training_paths(bundle, arguments.output_dir).models_root
        / "facial"
        / "embeddings"
        / config.dataset_version
        / "embeddings.parquet"
    )
    if arguments.dry_run:
        print(f"Destino: {destination}; no se escribieron artefactos.")
        return
    device = select_device(arguments.device)
    application = load_insightface(config, insightface_providers(device))
    frame = extract_embeddings(
        manifest,
        data_root=preparation.pipeline.paths.root,
        config=config,
        application=application,
    )
    save_embeddings(frame, destination)
    print(destination)


if __name__ == "__main__":
    main()
