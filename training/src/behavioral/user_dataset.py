from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.common.config import BehavioralTrainingConfig


@dataclass(frozen=True)
class UserBehaviorDataset:
    participant_id: str
    train: pd.DataFrame
    validation_genuine: pd.DataFrame
    validation_impostor: pd.DataFrame
    train_session_ids: tuple[str, ...]
    validation_session_ids: tuple[str, ...]


def build_user_dataset(
    frame: pd.DataFrame,
    participant_id: str,
    config: BehavioralTrainingConfig,
) -> UserBehaviorDataset | None:
    owner = frame["participant_id"].astype(str) == str(participant_id)
    legitimate = frame["operator_label"] == "legitimate"
    train = frame.loc[
        owner & legitimate & (frame["split"] == "train")
    ].copy()
    validation_genuine = frame.loc[
        owner & legitimate & (frame["split"] == "validation")
    ].copy()
    validation_changed_operator = frame.loc[
        owner
        & (frame["operator_label"] == "impostor")
        & (frame["split"] == "validation")
    ].copy()
    validation_other_users = frame.loc[
        ~owner & legitimate & (frame["split"] == "validation")
    ].copy()
    validation_impostor = pd.concat(
        [validation_changed_operator, validation_other_users], ignore_index=True
    )
    if (
        len(train) < config.minimum_train_windows_per_user
        or len(validation_genuine) < config.minimum_validation_windows_per_user
        or len(validation_impostor) < config.minimum_validation_impostor_windows
    ):
        return None
    validation_impostor = validation_impostor.sample(
        n=min(len(validation_impostor), max(len(validation_genuine) * 5, 1)),
        random_state=config.random_seed,
    ).reset_index(drop=True)
    return UserBehaviorDataset(
        participant_id=str(participant_id),
        train=train.reset_index(drop=True),
        validation_genuine=validation_genuine.reset_index(drop=True),
        validation_impostor=validation_impostor,
        train_session_ids=tuple(sorted(train["session_id"].astype(str).unique())),
        validation_session_ids=tuple(
            sorted(
                pd.concat([validation_genuine, validation_impostor])["session_id"]
                .astype(str)
                .unique()
            )
        ),
    )


def feature_matrix(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    matrix = frame[columns].to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(matrix).all():
        raise ValueError("La matriz conductual contiene NaN o infinito.")
    return matrix
