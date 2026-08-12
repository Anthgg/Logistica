from __future__ import annotations

from typing import Any

from src.common.config import PadTrainingConfig
from src.pad.augmentations import build_augmentation


def build_mobilenetv2(config: PadTrainingConfig) -> tuple[Any, Any]:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow no está instalado.") from exc
    inputs = tf.keras.Input(
        shape=(config.image_size.height, config.image_size.width, config.channels),
        name="image",
    )
    augmented = build_augmentation(config)(inputs)
    normalized = tf.keras.applications.mobilenet_v2.preprocess_input(augmented)
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(
            config.image_size.height,
            config.image_size.width,
            config.channels,
        ),
        include_top=config.include_top,
        weights="imagenet" if config.imagenet_weights else None,
    )
    backbone.trainable = False
    features = backbone(normalized, training=False)
    features = tf.keras.layers.GlobalAveragePooling2D(name="global_average_pool")(features)
    features = tf.keras.layers.Dropout(config.dropout, name="dropout")(features)
    if config.dense_units:
        features = tf.keras.layers.Dense(
            config.dense_units, activation="relu", name="classification_dense"
        )(features)
        features = tf.keras.layers.Dropout(
            config.dropout, name="classification_dropout"
        )(features)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="attack_probability")(
        features
    )
    return tf.keras.Model(inputs=inputs, outputs=outputs, name="pad_mobilenetv2"), backbone


def compile_pad_model(model: Any, learning_rate: float, label_smoothing: float) -> None:
    import tensorflow as tf

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss=tf.keras.losses.BinaryCrossentropy(label_smoothing=label_smoothing),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="accuracy"),
            tf.keras.metrics.AUC(name="roc_auc"),
            tf.keras.metrics.AUC(curve="PR", name="pr_auc"),
        ],
    )


def unfreeze_last_layers(backbone: Any, count: int) -> None:
    backbone.trainable = True
    boundary = max(0, len(backbone.layers) - count)
    for index, layer in enumerate(backbone.layers):
        layer.trainable = (
            index >= boundary and layer.__class__.__name__ != "BatchNormalization"
        )
