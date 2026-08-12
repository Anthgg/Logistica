import hashlib
import random

import pandas as pd

from src.common.config import SplitRatios

SPLITS = ("train", "validation", "test")


def _stable_seed(seed: int, value: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _allocation(count: int, ratios: SplitRatios) -> tuple[int, int, int]:
    if count <= 0:
        return 0, 0, 0
    if count == 1:
        return 1, 0, 0
    if count == 2:
        return 1, 0, 1
    validation = max(1, round(count * ratios.validation))
    test = max(1, round(count * ratios.test))
    train = count - validation - test
    if train < 1:
        train = 1
        if validation > test:
            validation -= 1
        else:
            test -= 1
    return train, validation, test


def assign_group_splits(
    frame: pd.DataFrame,
    *,
    group_column: str,
    ratios: SplitRatios,
    random_seed: int,
    participant_column: str = "participant_id",
) -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        if "split" not in result:
            result["split"] = pd.Series(dtype=str)
        return result
    if group_column not in result or participant_column not in result:
        raise ValueError("No existen las columnas de agrupación requeridas.")
    mapping: dict[str, str] = {}
    group_table = result[[participant_column, group_column]].drop_duplicates()
    for participant, participant_groups in group_table.groupby(
        participant_column, sort=True
    ):
        groups = sorted(str(value) for value in participant_groups[group_column])
        random.Random(_stable_seed(random_seed, str(participant))).shuffle(groups)
        train_count, validation_count, _ = _allocation(len(groups), ratios)
        for index, group in enumerate(groups):
            if index < train_count:
                split = "train"
            elif index < train_count + validation_count:
                split = "validation"
            else:
                split = "test"
            mapping[group] = split
    result["split"] = result[group_column].astype(str).map(mapping)
    if result["split"].isna().any():
        raise RuntimeError("No fue posible asignar todas las filas.")
    return result


def assign_pad_splits(
    frame: pd.DataFrame, *, ratios: SplitRatios, random_seed: int
) -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        result["split"] = pd.Series(dtype=str)
        return result
    group_columns = ["participant_id", "session_id"]
    if "source_device" in result:
        group_columns.append("source_device")
    if "pad_source_id" in result:
        group_columns.append("pad_source_id")
    result["_pad_group"] = result[group_columns].fillna("none").astype(str).agg(
        "|".join, axis=1
    )
    participants = sorted(result["participant_id"].astype(str).unique())
    random.Random(random_seed).shuffle(participants)
    train_count, validation_count, _ = _allocation(len(participants), ratios)
    participant_split = {
        participant: (
            "train"
            if index < train_count
            else "validation"
            if index < train_count + validation_count
            else "test"
        )
        for index, participant in enumerate(participants)
    }
    result["split"] = result["participant_id"].astype(str).map(participant_split)
    return result.drop(columns=["_pad_group"])


def split_summary(*manifests: tuple[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset_name, frame in manifests:
        if frame.empty or "split" not in frame:
            continue
        for split, count in frame.groupby("split").size().items():
            rows.append(
                {
                    "dataset": dataset_name,
                    "split": split,
                    "count": int(count),
                }
            )
    return pd.DataFrame(rows, columns=["dataset", "split", "count"])
