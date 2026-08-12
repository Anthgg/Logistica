import argparse
import json
from dataclasses import asdict

from _training import add_common_training_arguments, load_bundles
from src.common.device import select_device
from src.common.validation import TrainingInputError
from src.pipelines.train_all_pipeline import run_training_pipelines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entrena y calibra los componentes biométricos de Fase 8."
    )
    add_common_training_arguments(parser)
    parser.add_argument(
        "--models",
        choices=["facial", "pad", "behavioral", "all"],
        default="all",
    )
    arguments = parser.parse_args()
    preparation, bundle = load_bundles(
        arguments.config_dir,
        arguments.dataset_version,
        arguments.random_seed,
    )
    device = select_device(arguments.device)
    print(device.message)
    try:
        results = run_training_pipelines(
            preparation,
            bundle,
            models=arguments.models,
            device=device,
            output_dir=arguments.output_dir,
            participant_id=arguments.participant_id,
            experiment_name=arguments.experiment_name,
            dry_run=arguments.dry_run,
            resume=arguments.resume,
            force=arguments.force,
        )
    except TrainingInputError as exc:
        parser.exit(2, f"Entrenamiento bloqueado por validación:\n{exc}\n")
    print(
        json.dumps(
            [asdict(result) for result in results],
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
