import argparse

from _training import load_bundles
from src.experiments.report_builder import generate_training_report
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera informe desde resultados reales.")
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir")
    arguments = parser.parse_args()
    _, bundle = load_bundles(arguments.config_dir, arguments.dataset_version, None)
    paths = training_paths(bundle)
    destination = generate_training_report(
        report_root=paths.reports_root,
        models_root=paths.models_root,
        dataset_version=bundle.experiment.dataset_version,
        protocol_version=bundle.experiment.protocol_version,
    )
    print(destination)


if __name__ == "__main__":
    main()
