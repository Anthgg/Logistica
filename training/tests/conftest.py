import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

TRAINING_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("WINDIR", r"C:\Windows")
if str(TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(TRAINING_ROOT))

from src.common.config import (
    PreparationConfig,
    TrainingConfigBundle,
    load_config,
    load_training_configs,
)


@pytest.fixture
def config(tmp_path: Path) -> PreparationConfig:
    loaded = load_config()
    pipeline = loaded.pipeline.model_copy(
        update={
            "data_root": str(tmp_path / "data"),
            "capture_storage_root": str(tmp_path / "data" / "raw" / "facial"),
            "database_env_files": [],
        }
    )
    return loaded.model_copy(update={"pipeline": pipeline})


@pytest.fixture
def training_config() -> TrainingConfigBundle:
    return load_training_configs()


def sample_events(
    *,
    start: datetime | None = None,
    seconds: int = 70,
) -> list[dict[str, object]]:
    origin = start or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    events: list[dict[str, object]] = []
    sequence = 1
    for offset in range(0, seconds, 2):
        timestamp = origin + timedelta(seconds=offset)
        if offset % 4 == 0:
            events.append(
                {
                    "type": "keyboard",
                    "event": "timing",
                    "timestamp": timestamp.isoformat(),
                    "sequence_index": sequence,
                    "category": "alphanumeric",
                    "dwell_time_ms": 100.0,
                    "flight_time_ms": 50.0,
                    "interval_from_previous_ms": 200.0,
                    "is_backspace": False,
                    "is_modifier": False,
                }
            )
        else:
            events.append(
                {
                    "type": "mouse",
                    "event": "move",
                    "timestamp": timestamp.isoformat(),
                    "sequence_index": sequence,
                    "normalized_x": min(0.95, 0.1 + offset / 100),
                    "normalized_y": min(0.95, 0.2 + offset / 120),
                    "delta_x": 0.02,
                    "delta_y": 0.01,
                    "distance": 0.02,
                    "velocity": 0.01,
                }
            )
        sequence += 1
    return events


@pytest.fixture
def valid_batch() -> dict[str, object]:
    start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    return {
        "participant_id": "participant-1",
        "session_id": "session-1",
        "scenario": "mixed_operations",
        "session_started_at": start,
        "session_ended_at": start + timedelta(seconds=70),
        "started_at": start,
        "ended_at": start + timedelta(seconds=70),
        "batch_id": "batch-1",
        "sequence_number": 1,
        "payload": sample_events(start=start),
    }


@pytest.fixture
def event_frame(valid_batch: dict[str, object]) -> pd.DataFrame:
    rows = []
    for event in valid_batch["payload"]:
        rows.append(
            {
                "participant_id": valid_batch["participant_id"],
                "session_id": valid_batch["session_id"],
                "scenario": valid_batch["scenario"],
                "session_started_at": valid_batch["session_started_at"],
                "session_ended_at": valid_batch["session_ended_at"],
                "batch_id": valid_batch["batch_id"],
                **event,
            }
        )
    return pd.DataFrame(rows)
