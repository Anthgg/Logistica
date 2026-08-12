from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import BehavioralTrainingConfig
from src.common.validation import development_rows, require_columns

METADATA_COLUMNS = {
    "dataset_version",
    "protocol_version",
    "participant_id",
    "session_id",
    "window_id",
    "operator_label",
    "quality_status",
    "split",
}


def load_behavioral_features(
    path: Path, config: BehavioralTrainingConfig
) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    require_columns(
        frame,
        METADATA_COLUMNS | set(config.feature_columns),
        "behavioral_features",
    )
    selected = development_rows(frame, dataset_version=config.dataset_version)
    unknown = set(selected["operator_label"].astype(str)) - {"legitimate", "impostor"}
    if unknown:
        raise ValueError(f"operator_label desconocido: {sorted(unknown)}.")
    return selected
