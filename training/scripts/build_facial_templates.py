import argparse

import pandas as pd

from _training import add_common_training_arguments, load_bundles
from src.facial.template_builder import build_participant_templates
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Construye plantillas faciales con train.")
    add_common_training_arguments(parser)
    arguments = parser.parse_args()
    _, bundle = load_bundles(
        arguments.config_dir, arguments.dataset_version, arguments.random_seed
    )
    paths = training_paths(bundle, arguments.output_dir)
    embeddings_path = (
        paths.models_root
        / "facial"
        / "embeddings"
        / bundle.arcface.dataset_version
        / "embeddings.parquet"
    )
    embeddings = pd.read_parquet(embeddings_path)
    destination = (
        paths.models_root
        / "facial"
        / "templates"
        / bundle.arcface.dataset_version
    )
    if arguments.dry_run:
        print(f"Destino: {destination}; no se escribieron artefactos.")
        return
    artifacts, rejected = build_participant_templates(
        embeddings,
        output_dir=destination,
        config=bundle.arcface,
        config_payload=bundle.arcface.model_dump(mode="json"),
    )
    print(f"Plantillas: {len(artifacts)}; rechazados: {len(rejected)}")


if __name__ == "__main__":
    main()
