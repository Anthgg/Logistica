from pathlib import Path

from PIL import Image
import pandas as pd

from src.common.hashing import sha256_file
from src.pad.dataset_loader import load_pad_frame


def test_loads_train_validation_and_excludes_test(tmp_path, training_config) -> None:
    rows = []
    definitions = (
        ("train", "attack", "printed_photo"),
        ("train", "bona_fide", "none"),
        ("validation", "attack", "screen_photo"),
        ("validation", "bona_fide", "none"),
        ("test", "attack", "replayed_video"),
        ("test", "bona_fide", "none"),
    )
    for index, (split, label, attack_type) in enumerate(definitions, start=1):
        path = tmp_path / f"image-{index}.jpg"
        Image.new("RGB", (16, 16), color=(index, index, index)).save(path)
        rows.append(
            {
                "participant_id": f"P{index}",
                "session_id": f"s{index}",
                "capture_id": f"c{index}",
                "file_path": path.name,
                "checksum": sha256_file(path),
                "presentation_label": label,
                "attack_type": attack_type,
                "quality_status": "accepted",
                "dataset_version": "pilot-v0.1.0",
                "split": split,
            }
        )
    manifest = tmp_path / "pad.parquet"
    pd.DataFrame(rows).to_parquet(manifest, index=False)
    frame = load_pad_frame(
        manifest, data_root=tmp_path, config=training_config.pad
    )
    assert set(frame["split"]) == {"train", "validation"}
    assert len(frame) == 4
