from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

from evaluation.src.common.config import load_config
from evaluation.src.common.integrity import preflight


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica compuertas y sidecars sin abrir el manifiesto test. "
            "La verificación completa solo ocurre dentro del ejecutor final "
            "después del lock y el marcador de inicio."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evaluation/configs/final_evaluation.yaml"),
    )
    arguments = parser.parse_args()
    result = preflight(load_config(arguments.config))
    print(json.dumps(result.as_json(), ensure_ascii=False, indent=2))
    if not result.approved:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
