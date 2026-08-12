from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytest

from src.common.hashing import sha256_file
from src.facial.embedding_extractor import extract_embeddings
from src.facial.face_preprocessor import FaceRejection, extract_single_face, l2_normalize


@dataclass
class FakeFace:
    normed_embedding: np.ndarray
    det_score: float = 0.99


class FakeApplication:
    def __init__(self, faces):
        self.faces = faces

    def get(self, image):
        assert image.ndim == 3
        return self.faces


def test_normalizes_embedding_and_rejects_invalid_faces() -> None:
    vector = l2_normalize(np.array([3.0, 4.0]))
    assert np.linalg.norm(vector) == pytest.approx(1.0)
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    with pytest.raises(FaceRejection, match="NO_FACE"):
        extract_single_face(
            FakeApplication([]),
            image,
            minimum_detection_score=0.5,
            embedding_dimension=2,
        )
    with pytest.raises(FaceRejection, match="MULTIPLE_FACES"):
        extract_single_face(
            FakeApplication([FakeFace(vector), FakeFace(vector)]),
            image,
            minimum_detection_score=0.5,
            embedding_dimension=2,
        )


def test_extracts_only_train_and_validation(tmp_path, training_config) -> None:
    image_path = tmp_path / "face.jpg"
    cv2.imwrite(str(image_path), np.zeros((32, 32, 3), dtype=np.uint8))
    checksum = sha256_file(image_path)
    rows = []
    for split, capture in (("train", "c1"), ("validation", "c2"), ("test", "c3")):
        rows.append(
            {
                "participant_id": "P-0001",
                "session_id": f"s-{split}",
                "capture_id": capture,
                "split": split,
                "sample_role": "enrollment" if split == "train" else "verification",
                "identity_label": "genuine",
                "file_path": "face.jpg",
                "checksum": checksum,
                "dataset_version": "pilot-v0.1.0",
                "quality_status": "accepted",
            }
        )
    config = training_config.arcface.model_copy(update={"embedding_dimension": 2})
    extracted = extract_embeddings(
        pd.DataFrame(rows),
        data_root=tmp_path,
        config=config,
        application=FakeApplication([FakeFace(np.array([3.0, 4.0]))]),
    )
    assert set(extracted["split"]) == {"train", "validation"}
    assert set(extracted["extraction_status"]) == {"accepted"}
    assert all(
        np.linalg.norm(np.asarray(value)) == pytest.approx(1.0)
        for value in extracted["embedding"]
    )
