from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import pandas as pd

from src.common.config import ArcFaceTrainingConfig
from src.common.hashing import sha256_file
from src.common.validation import development_rows, require_columns
from src.facial.face_preprocessor import FaceRejection, extract_single_face

EMBEDDING_COLUMNS = [
    "participant_id",
    "session_id",
    "capture_id",
    "split",
    "sample_role",
    "identity_label",
    "embedding",
    "detection_score",
    "extraction_status",
    "rejection_reason",
    "model_name",
    "model_version",
    "checksum",
]


def extract_embeddings(
    manifest: pd.DataFrame,
    *,
    data_root: Path,
    config: ArcFaceTrainingConfig,
    application: Any,
) -> pd.DataFrame:
    require_columns(
        manifest,
        {
            "participant_id",
            "session_id",
            "capture_id",
            "split",
            "sample_role",
            "identity_label",
            "file_path",
            "checksum",
            "dataset_version",
            "quality_status",
        },
        "facial_identity_manifest",
    )
    selected = development_rows(manifest, dataset_version=config.dataset_version)
    rows: list[dict[str, object]] = []
    for record in selected.sort_values(["participant_id", "session_id", "capture_id"]).to_dict(
        orient="records"
    ):
        relative = Path(str(record["file_path"]))
        rejection: str | None = None
        result = None
        if relative.is_absolute() or ".." in relative.parts:
            rejection = "UNSAFE_FILE_PATH"
        else:
            image_path = data_root / relative
            if not image_path.is_file():
                rejection = "FILE_NOT_FOUND"
            elif sha256_file(image_path) != str(record["checksum"]):
                rejection = "CHECKSUM_MISMATCH"
            else:
                image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
                if image is None:
                    rejection = "INVALID_IMAGE"
                else:
                    try:
                        result = extract_single_face(
                            application,
                            image,
                            minimum_detection_score=config.minimum_detection_score,
                            embedding_dimension=config.embedding_dimension,
                        )
                    except FaceRejection as exc:
                        rejection = exc.reason
        rows.append(
            {
                "participant_id": str(record["participant_id"]),
                "session_id": str(record["session_id"]),
                "capture_id": str(record["capture_id"]),
                "split": str(record["split"]),
                "sample_role": str(record["sample_role"]),
                "identity_label": str(record["identity_label"]),
                "embedding": result.embedding.tolist() if result else None,
                "detection_score": result.detection_score if result else None,
                "extraction_status": "accepted" if result else "rejected",
                "rejection_reason": rejection,
                "model_name": config.model_name,
                "model_version": config.model_version,
                "checksum": str(record["checksum"]),
            }
        )
    return pd.DataFrame(rows, columns=EMBEDDING_COLUMNS)


def save_embeddings(frame: pd.DataFrame, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(destination, index=False)
    return destination
