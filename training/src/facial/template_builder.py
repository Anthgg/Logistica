from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.config import ArcFaceTrainingConfig
from src.common.serialization import configuration_checksum, write_json_atomic
from src.common.hashing import sha256_file
from src.facial.face_preprocessor import l2_normalize


@dataclass(frozen=True)
class TemplateArtifact:
    participant_id: str
    template_path: Path
    metadata_path: Path
    enrollment_capture_count: int


def build_template(embeddings: list[np.ndarray]) -> np.ndarray:
    if not embeddings:
        raise ValueError("Se requiere al menos un embedding.")
    normalized = np.stack([l2_normalize(item) for item in embeddings])
    return l2_normalize(np.mean(normalized, axis=0))


def build_participant_templates(
    embeddings: pd.DataFrame,
    *,
    output_dir: Path,
    config: ArcFaceTrainingConfig,
    config_payload: dict[str, object],
) -> tuple[list[TemplateArtifact], list[dict[str, object]]]:
    accepted = embeddings.loc[
        (embeddings["split"] == "train")
        & (embeddings["sample_role"] == "enrollment")
        & (embeddings["extraction_status"] == "accepted")
    ].copy()
    artifacts: list[TemplateArtifact] = []
    rejected: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for participant_id, group in accepted.groupby("participant_id", sort=True):
        group = group.sort_values(["session_id", "capture_id"]).head(
            config.maximum_enrollment_images
        )
        if len(group) < config.minimum_enrollment_images:
            rejected.append(
                {
                    "participant_id": str(participant_id),
                    "reason": "INSUFFICIENT_ENROLLMENT_IMAGES",
                    "available": int(len(group)),
                    "required": config.minimum_enrollment_images,
                }
            )
            continue
        template = build_template(
            [np.asarray(item, dtype=np.float32) for item in group["embedding"]]
        )
        template_path = output_dir / f"{participant_id}.npz"
        np.savez_compressed(template_path, template=template)
        metadata_path = output_dir / f"{participant_id}.json"
        payload = {
            "participant_id": str(participant_id),
            "dataset_version": config.dataset_version,
            "model_name": config.model_name,
            "embedding_dimension": int(template.size),
            "template_strategy": config.template_strategy,
            "enrollment_session_ids": sorted(group["session_id"].astype(str).unique()),
            "enrollment_capture_count": int(len(group)),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "template_checksum": sha256_file(template_path),
            "config_checksum": configuration_checksum(config_payload),
        }
        write_json_atomic(metadata_path, payload)
        artifacts.append(
            TemplateArtifact(
                participant_id=str(participant_id),
                template_path=template_path,
                metadata_path=metadata_path,
                enrollment_capture_count=len(group),
            )
        )
    return artifacts, rejected


def load_templates(directory: Path) -> dict[str, np.ndarray]:
    templates: dict[str, np.ndarray] = {}
    for path in sorted(directory.glob("*.npz")):
        with np.load(path, allow_pickle=False) as content:
            templates[path.stem] = l2_normalize(content["template"])
    return templates
