import argparse
import json

from _training import load_bundles
from src.common.validation import validate_training_inputs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida entradas de Fase 8 sin leer datos test para entrenamiento."
    )
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir")
    arguments = parser.parse_args()
    preparation, bundle = load_bundles(
        arguments.config_dir, arguments.dataset_version, None
    )
    report = validate_training_inputs(preparation, bundle)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, default=str))
    if not report.valid:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
