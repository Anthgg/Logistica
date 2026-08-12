from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from src.common.config import (
    PreparationConfig,
    TrainingConfigBundle,
    load_config,
    load_training_configs,
)
from src.common.reproducibility import configure_reproducibility


def load_bundles(
    config_dir: str | None,
    dataset_version: str | None,
    random_seed: int | None,
) -> tuple[PreparationConfig, TrainingConfigBundle]:
    preparation = load_config(config_dir)
    bundle = load_training_configs(config_dir)
    expected = bundle.experiment.dataset_version
    if dataset_version and dataset_version != expected:
        raise ValueError(
            f"Se solicitó {dataset_version}, pero las configuraciones usan {expected}."
        )
    if random_seed is not None:
        bundle = bundle.model_copy(
            update={
                "arcface": bundle.arcface.model_copy(
                    update={"random_seed": random_seed}
                ),
                "pad": bundle.pad.model_copy(update={"random_seed": random_seed}),
                "behavioral": bundle.behavioral.model_copy(
                    update={"random_seed": random_seed}
                ),
                "experiment": bundle.experiment.model_copy(
                    update={"random_seed": random_seed}
                ),
            }
        )
    configure_reproducibility(
        bundle.experiment.random_seed,
        bundle.experiment.deterministic_operations,
    )
    return preparation, bundle


def add_common_training_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir", help="Directorio de configuraciones YAML.")
    parser.add_argument("--output-dir", type=Path, help="Sobrescribe models/.")
    parser.add_argument("--participant-id", help="Participante seudonimizado.")
    parser.add_argument("--experiment-name")
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--random-seed", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
