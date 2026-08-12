from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.utils.class_weight import compute_class_weight

from src.common.config import PadTrainingConfig
from src.common.hashing import sha256_file
from src.common.validation import development_rows, require_columns

PAD_REQUIRED_COLUMNS = {
    "participant_id",
    "session_id",
    "capture_id",
    "file_path",
    "checksum",
    "presentation_label",
    "attack_type",
    "quality_status",
    "dataset_version",
    "split",
}


def load_pad_frame(
    manifest_path: Path,
    *,
    data_root: Path,
    config: PadTrainingConfig,
) -> pd.DataFrame:
    frame = pd.read_parquet(manifest_path)
    require_columns(frame, PAD_REQUIRED_COLUMNS, "facial_pad_manifest")
    selected = development_rows(frame, dataset_version=config.dataset_version)
    unknown = set(selected["presentation_label"]) - {"bona_fide", "attack"}
    if unknown:
        raise ValueError(f"Etiquetas PAD desconocidas: {sorted(unknown)}.")
    rows: list[dict[str, object]] = []
    for record in selected.to_dict(orient="records"):
        relative = Path(str(record["file_path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Ruta PAD insegura: {relative}.")
        image_path = data_root / relative
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        if sha256_file(image_path) != str(record["checksum"]):
            raise ValueError(f"Checksum PAD incorrecto: {relative}.")
        rows.append(
            {
                **record,
                "_image_path": str(image_path.resolve()),
                "label": 1 if record["presentation_label"] == "attack" else 0,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty or set(result["split"]) != {"train", "validation"}:
        raise ValueError("PAD requiere muestras aceptadas de train y validation.")
    for split in ("train", "validation"):
        if set(result.loc[result["split"] == split, "label"].astype(int)) != {0, 1}:
            raise ValueError(f"PAD requiere bona_fide y attack en {split}.")
    return result


def class_weights(frame: pd.DataFrame) -> dict[int, float] | None:
    labels = frame.loc[frame["split"] == "train", "label"].astype(int).to_numpy()
    classes = np.unique(labels)
    if len(classes) != 2:
        return None
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=labels)
    return {int(label): float(weight) for label, weight in zip(classes, weights)}


def build_tf_dataset(
    frame: pd.DataFrame,
    *,
    config: PadTrainingConfig,
    training: bool,
) -> Any:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow no está instalado.") from exc
    split = "train" if training else "validation"
    selected = frame.loc[frame["split"] == split].copy()
    if selected.empty:
        raise ValueError(f"No existen muestras PAD de {split}.")
    paths = selected["_image_path"].astype(str).to_numpy()
    labels = selected["label"].astype(np.float32).to_numpy()
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))

    def read_with_pillow(path_value: Any) -> np.ndarray:
        path = path_value.numpy().decode("utf-8")
        with Image.open(path) as source:
            return np.asarray(source.convert("RGB"), dtype=np.float32)

    def decode(path: Any, label: Any) -> tuple[Any, Any]:
        image = tf.py_function(read_with_pillow, [path], Tout=tf.float32)
        image.set_shape([None, None, config.channels])
        image = tf.image.resize(
            image, [config.image_size.height, config.image_size.width]
        )
        return tf.cast(image, tf.float32), tf.cast(label, tf.float32)

    dataset = dataset.map(decode, num_parallel_calls=tf.data.AUTOTUNE)
    if training:
        dataset = dataset.shuffle(
            buffer_size=len(selected),
            seed=config.random_seed,
            reshuffle_each_iteration=True,
        )
    if config.cache_dataset:
        dataset = dataset.cache()
    return dataset.batch(config.batch_size).prefetch(tf.data.AUTOTUNE)
