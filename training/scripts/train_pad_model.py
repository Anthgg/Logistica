import argparse
import json
from dataclasses import asdict

from _training import add_common_training_arguments, load_bundles
from src.common.device import select_device
from src.pipelines.train_pad_pipeline import run_pad_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena MobileNetV2 PAD.")
    add_common_training_arguments(parser)
    arguments = parser.parse_args()
    preparation, bundle = load_bundles(
        arguments.config_dir, arguments.dataset_version, arguments.random_seed
    )
    result = run_pad_pipeline(
        preparation,
        bundle,
        device=select_device(arguments.device),
        output_dir=arguments.output_dir,
        dry_run=arguments.dry_run,
        resume=arguments.resume,
        force=arguments.force,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
