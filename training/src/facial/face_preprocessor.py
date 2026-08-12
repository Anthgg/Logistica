from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


class FaceRejection(ValueError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class FaceEmbedding:
    embedding: np.ndarray
    detection_score: float


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(value))
    if not np.isfinite(norm) or norm <= 0:
        raise FaceRejection("INVALID_EMBEDDING")
    return value / norm


def extract_single_face(
    application: Any,
    image_bgr: np.ndarray,
    *,
    minimum_detection_score: float,
    embedding_dimension: int,
) -> FaceEmbedding:
    faces = application.get(image_bgr)
    if not faces:
        raise FaceRejection("NO_FACE")
    if len(faces) != 1:
        raise FaceRejection("MULTIPLE_FACES")
    face = faces[0]
    score = float(getattr(face, "det_score", 0.0))
    if not np.isfinite(score) or score < minimum_detection_score:
        raise FaceRejection("LOW_DETECTION_SCORE")
    embedding = getattr(face, "normed_embedding", None)
    if embedding is None:
        embedding = getattr(face, "embedding", None)
    if embedding is None:
        raise FaceRejection("MISSING_EMBEDDING")
    normalized = l2_normalize(np.asarray(embedding))
    if normalized.size != embedding_dimension:
        raise FaceRejection("INVALID_EMBEDDING_DIMENSION")
    return FaceEmbedding(embedding=normalized, detection_score=score)
