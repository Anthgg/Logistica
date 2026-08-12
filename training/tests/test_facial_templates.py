import json

import numpy as np
import pandas as pd
import pytest

from src.facial.template_builder import build_participant_templates, build_template


def test_builds_normalized_template() -> None:
    template = build_template(
        [np.array([1.0, 0.0]), np.array([0.8, 0.2])]
    )
    assert np.linalg.norm(template) == pytest.approx(1.0)


def test_exports_template_with_pseudonymous_metadata(tmp_path, training_config) -> None:
    config = training_config.arcface.model_copy(
        update={"embedding_dimension": 2, "minimum_enrollment_images": 2}
    )
    frame = pd.DataFrame(
        [
            {
                "participant_id": "P-0001",
                "session_id": "s1",
                "capture_id": "c1",
                "split": "train",
                "sample_role": "enrollment",
                "extraction_status": "accepted",
                "embedding": [1.0, 0.0],
            },
            {
                "participant_id": "P-0001",
                "session_id": "s2",
                "capture_id": "c2",
                "split": "train",
                "sample_role": "enrollment",
                "extraction_status": "accepted",
                "embedding": [0.9, 0.1],
            },
        ]
    )
    artifacts, rejected = build_participant_templates(
        frame,
        output_dir=tmp_path,
        config=config,
        config_payload=config.model_dump(mode="json"),
    )
    assert not rejected
    assert len(artifacts) == 1
    metadata = json.loads(artifacts[0].metadata_path.read_text(encoding="utf-8"))
    assert metadata["participant_id"] == "P-0001"
    assert "email" not in metadata
    assert metadata["enrollment_capture_count"] == 2
