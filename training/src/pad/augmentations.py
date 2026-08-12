from __future__ import annotations

from typing import Any

from src.common.config import PadTrainingConfig


def build_augmentation(config: PadTrainingConfig) -> Any:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow no está instalado.") from exc
    augmentation = config.augmentation
    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomRotation(
                augmentation.rotation, seed=config.random_seed
            ),
            tf.keras.layers.RandomTranslation(
                augmentation.translation,
                augmentation.translation,
                seed=config.random_seed + 1,
            ),
            tf.keras.layers.RandomZoom(
                height_factor=(-augmentation.zoom, augmentation.zoom),
                width_factor=(-augmentation.zoom, augmentation.zoom),
                seed=config.random_seed + 2,
            ),
            tf.keras.layers.RandomContrast(
                augmentation.contrast, seed=config.random_seed + 3
            ),
            tf.keras.layers.RandomBrightness(
                augmentation.brightness,
                value_range=(0.0, 255.0),
                seed=config.random_seed + 4,
            ),
        ],
        name="train_only_augmentation",
    )
