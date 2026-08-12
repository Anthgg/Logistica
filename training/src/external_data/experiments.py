from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from src.common.metrics import binary_metrics, threshold_candidates
from src.common.serialization import write_json_atomic


class ExperimentGateError(RuntimeError):
    """Un experimento intentó usar datos fuera de su protocolo."""


@dataclass(frozen=True)
class DatasetUse:
    dataset: str
    split: Literal["train", "validation", "test"]


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_id: str
    family: Literal["pad", "behavioral"]
    training: tuple[DatasetUse, ...]
    fine_tuning: tuple[DatasetUse, ...]
    validation: tuple[DatasetUse, ...]
    test: tuple[DatasetUse, ...]
    calibration_source: Literal["validation", "none"]
    selection_source: Literal["validation"]
    protocol_notes: tuple[str, ...]
    consumes_frozen_own_test: bool = False


PAD_PLANS = (
    ExperimentPlan(
        experiment_id="PAD-A-public-generalization",
        family="pad",
        training=(DatasetUse("celeba_spoof", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("replay_attack", "validation"),),
        test=(DatasetUse("oulu_npu", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=(
            "Respeta los splits oficiales.",
            "El umbral no se recalibra con OULU-NPU test.",
        ),
    ),
    ExperimentPlan(
        experiment_id="PAD-B-own-only",
        family="pad",
        training=(DatasetUse("own_pad", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("own_pad", "validation"),),
        test=(DatasetUse("own_pad", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=("Test propio congelado: una sola evaluación aprobada.",),
        consumes_frozen_own_test=True,
    ),
    ExperimentPlan(
        experiment_id="PAD-C-public-own-finetune",
        family="pad",
        training=(
            DatasetUse("celeba_spoof", "train"),
            DatasetUse("replay_attack", "train"),
        ),
        fine_tuning=(DatasetUse("own_pad", "train"),),
        validation=(DatasetUse("own_pad", "validation"),),
        test=(DatasetUse("own_pad", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=(
            "Fine-tuning solo con train propio.",
            "Candidato principal; test propio congelado requiere aprobación.",
        ),
        consumes_frozen_own_test=True,
    ),
    ExperimentPlan(
        experiment_id="PAD-D-replay-to-oulu",
        family="pad",
        training=(DatasetUse("replay_attack", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("replay_attack", "validation"),),
        test=(DatasetUse("oulu_npu", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=("Sin recalibración sobre OULU-NPU test.",),
    ),
    ExperimentPlan(
        experiment_id="PAD-D-oulu-to-replay",
        family="pad",
        training=(DatasetUse("oulu_npu", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("oulu_npu", "validation"),),
        test=(DatasetUse("replay_attack", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=("Sin recalibración sobre Replay-Attack test.",),
    ),
    ExperimentPlan(
        experiment_id="PAD-D-celeba-to-replay",
        family="pad",
        training=(DatasetUse("celeba_spoof", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("celeba_spoof", "validation"),),
        test=(DatasetUse("replay_attack", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=("Sin recalibración sobre Replay-Attack test.",),
    ),
)

BEHAVIORAL_PLANS = (
    ("CONDUCTUAL-A-CMU", "cmu_keystroke", "keyboard", "texto fijo"),
    ("CONDUCTUAL-B-AALTO", "aalto_keystrokes", "keyboard", "texto libre; teclas eliminadas"),
    ("CONDUCTUAL-C-BALABIT", "balabit_mouse", "mouse", "sesiones de escritorio remoto"),
    (
        "CONDUCTUAL-D-KMT",
        "behaviour_biometrics",
        "keyboard_mouse",
        "formulario con datos ficticios",
    ),
    (
        "CONDUCTUAL-E-OWN",
        "own_behavioral",
        "keyboard_mouse",
        "un autoencoder por participante; único candidato directo",
    ),
)


def validate_experiment_plan(
    plan: ExperimentPlan, *, frozen_test_approval: bool = False
) -> None:
    calibration_datasets = {item.dataset for item in plan.validation}
    test_datasets = {item.dataset for item in plan.test}
    if plan.calibration_source != "none" and calibration_datasets & test_datasets:
        overlapping = calibration_datasets & test_datasets
        validation_splits = {
            (item.dataset, item.split) for item in plan.validation if item.dataset in overlapping
        }
        test_splits = {
            (item.dataset, item.split) for item in plan.test if item.dataset in overlapping
        }
        if validation_splits & test_splits:
            raise ExperimentGateError("No se puede calibrar con el mismo split de test.")
    if any(item.split != "train" for item in plan.training):
        raise ExperimentGateError("El entrenamiento solo puede consumir splits train.")
    if any(
        item.dataset != "own_pad" or item.split != "train" for item in plan.fine_tuning
    ):
        raise ExperimentGateError("Fine-tuning PAD solo puede usar train propio.")
    if plan.selection_source != "validation":
        raise ExperimentGateError("La selección de modelo debe usar validation.")
    if plan.consumes_frozen_own_test and not frozen_test_approval:
        raise ExperimentGateError(
            "El test propio congelado permanece bloqueado sin aprobación explícita."
        )


def serializable_plan(plan: ExperimentPlan) -> dict[str, object]:
    return asdict(plan)


def write_experiment_plans(
    output_path: str | Path,
    *,
    family: Literal["pad", "behavioral"],
) -> Path:
    if family == "pad":
        plans: list[object] = [serializable_plan(plan) for plan in PAD_PLANS]
    else:
        plans = [
            {
                "experiment_id": experiment_id,
                "dataset": dataset,
                "modality": modality,
                "protocol_notes": notes,
                "selection_source": "validation",
                "test_used_for_calibration": False,
            }
            for experiment_id, dataset, modality, notes in BEHAVIORAL_PLANS
        ]
    target = Path(output_path)
    write_json_atomic(target, {"family": family, "plans": plans, "status": "planned"})
    return target


def pad_metrics(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
    *,
    threshold: float,
) -> dict[str, object]:
    metrics = binary_metrics(labels, scores, threshold)
    confusion = np.asarray(metrics["confusion_matrix"], dtype=int)
    true_negative, false_positive, false_negative, true_positive = confusion.ravel()
    apcer = false_negative / max(1, false_negative + true_positive)
    bpcer = false_positive / max(1, true_negative + false_positive)
    candidates = threshold_candidates(labels, scores)
    eer_candidate = min(candidates, key=lambda item: abs(item.far - item.frr))
    return {
        **metrics,
        "APCER": float(apcer),
        "BPCER": float(bpcer),
        "ACER": float((apcer + bpcer) / 2),
        "EER": float((eer_candidate.far + eer_candidate.frr) / 2),
    }


def behavioral_metrics(
    labels: np.ndarray | list[int],
    anomaly_scores: np.ndarray | list[float],
    *,
    threshold: float,
) -> dict[str, object]:
    metrics = binary_metrics(
        labels, anomaly_scores, threshold, positive_direction="lower"
    )
    candidates = threshold_candidates(
        labels, anomaly_scores, positive_direction="lower"
    )
    eer_candidate = min(candidates, key=lambda item: abs(item.far - item.frr))
    return {
        **metrics,
        "FAR": float(eer_candidate.far),
        "FRR": float(eer_candidate.frr),
        "EER": float((eer_candidate.far + eer_candidate.frr) / 2),
    }


def assert_manifest_supports_plan(
    manifest: pd.DataFrame, plan: ExperimentPlan
) -> None:
    required = {"source_dataset", "split_project", "license_status"}
    missing = required - set(manifest.columns)
    if missing:
        raise ExperimentGateError(f"Manifiesto incompleto: {sorted(missing)}")
    for usage in (*plan.training, *plan.fine_tuning, *plan.validation, *plan.test):
        rows = manifest[
            (manifest["source_dataset"] == usage.dataset)
            & (manifest["split_project"] == usage.split)
            & (manifest["license_status"].isin(["approved", "downloaded"]))
        ]
        if rows.empty:
            raise ExperimentGateError(
                f"{plan.experiment_id}: faltan filas aprobadas para "
                f"{usage.dataset}/{usage.split}."
            )
