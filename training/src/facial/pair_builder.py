from __future__ import annotations

import numpy as np
import pandas as pd

from src.facial.face_preprocessor import l2_normalize

PAIR_COLUMNS = [
    "template_participant_id",
    "sample_participant_id",
    "session_id",
    "capture_id",
    "pair_type",
    "label",
    "similarity",
]


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    normalized_left = l2_normalize(left)
    normalized_right = l2_normalize(right)
    return float(np.dot(normalized_left, normalized_right))


def build_validation_pairs(
    templates: dict[str, np.ndarray],
    embeddings: pd.DataFrame,
    *,
    maximum_impostor_pairs_per_identity: int,
    random_seed: int,
) -> pd.DataFrame:
    validation = embeddings.loc[
        (embeddings["split"] == "validation")
        & (embeddings["extraction_status"] == "accepted")
    ].copy()
    rows: list[dict[str, object]] = []
    for template_participant, template in sorted(templates.items()):
        for record in validation.sort_values(["participant_id", "capture_id"]).to_dict(
            orient="records"
        ):
            sample_participant = str(record["participant_id"])
            genuine = sample_participant == template_participant
            rows.append(
                {
                    "template_participant_id": template_participant,
                    "sample_participant_id": sample_participant,
                    "session_id": str(record["session_id"]),
                    "capture_id": str(record["capture_id"]),
                    "pair_type": "genuine" if genuine else "impostor",
                    "label": 1 if genuine else 0,
                    "similarity": cosine_similarity(
                        template, np.asarray(record["embedding"], dtype=np.float32)
                    ),
                }
            )
    pairs = pd.DataFrame(rows, columns=PAIR_COLUMNS)
    if pairs.empty:
        return pairs
    genuine = pairs[pairs["pair_type"] == "genuine"]
    impostor_groups: list[pd.DataFrame] = []
    for _, group in pairs[pairs["pair_type"] == "impostor"].groupby(
        "template_participant_id", sort=True
    ):
        count = min(maximum_impostor_pairs_per_identity, len(group))
        impostor_groups.append(group.sample(n=count, random_state=random_seed))
    impostors = (
        pd.concat(impostor_groups, ignore_index=True)
        if impostor_groups
        else pd.DataFrame(columns=PAIR_COLUMNS)
    )
    result = pd.concat([genuine, impostors], ignore_index=True)
    result = result.drop_duplicates(
        ["template_participant_id", "capture_id"], keep="first"
    )
    return result.sort_values(
        ["template_participant_id", "pair_type", "capture_id"]
    ).reset_index(drop=True)
