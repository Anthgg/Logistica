import pandas as pd

from src.facial.facial_threshold import calibrate_facial_threshold
from src.facial.pair_builder import build_validation_pairs


def test_creates_unique_genuine_and_impostor_pairs() -> None:
    templates = {"P1": [1.0, 0.0], "P2": [0.0, 1.0]}
    embeddings = pd.DataFrame(
        [
            {
                "participant_id": "P1",
                "session_id": "s1",
                "capture_id": "c1",
                "split": "validation",
                "extraction_status": "accepted",
                "embedding": [0.9, 0.1],
            },
            {
                "participant_id": "P2",
                "session_id": "s2",
                "capture_id": "c2",
                "split": "validation",
                "extraction_status": "accepted",
                "embedding": [0.1, 0.9],
            },
        ]
    )
    pairs = build_validation_pairs(
        templates,
        embeddings,
        maximum_impostor_pairs_per_identity=10,
        random_seed=42,
    )
    assert set(pairs["pair_type"]) == {"genuine", "impostor"}
    assert not pairs.duplicated(["template_participant_id", "capture_id"]).any()


def test_calibrates_facial_threshold_from_validation(training_config) -> None:
    pairs = pd.DataFrame(
        {
            "label": [1, 1, 0, 0],
            "similarity": [0.9, 0.8, 0.2, 0.1],
        }
    )
    payload = calibrate_facial_threshold(
        pairs,
        training_config.arcface,
        training_config.arcface.model_dump(mode="json"),
    )
    assert 0.2 <= payload["selected_threshold"] <= 0.9
    assert payload["validation_eer"] == 0.0
    assert payload["test_rows_used"] == 0
