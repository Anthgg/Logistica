import argparse

import pandas as pd

from _training import add_common_training_arguments, load_bundles
from src.common.serialization import write_json_atomic
from src.facial.facial_threshold import calibrate_facial_threshold
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibra el umbral facial con validation.")
    add_common_training_arguments(parser)
    arguments = parser.parse_args()
    _, bundle = load_bundles(
        arguments.config_dir, arguments.dataset_version, arguments.random_seed
    )
    paths = training_paths(bundle, arguments.output_dir)
    pairs = pd.read_parquet(paths.reports_root / "facial" / "validation_pairs.parquet")
    payload = calibrate_facial_threshold(
        pairs, bundle.arcface, bundle.arcface.model_dump(mode="json")
    )
    destination = (
        paths.models_root
        / "facial"
        / "thresholds"
        / bundle.arcface.dataset_version
        / "facial_threshold.json"
    )
    if not arguments.dry_run:
        write_json_atomic(destination, payload)
    print(payload)


if __name__ == "__main__":
    main()
