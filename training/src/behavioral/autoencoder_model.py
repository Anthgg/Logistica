from __future__ import annotations

from typing import Any

from src.common.config import BehavioralTrainingConfig


def build_autoencoder(
    input_dimension: int, config: BehavioralTrainingConfig
) -> Any:
    if input_dimension <= 0:
        raise ValueError("input_dimension debe ser positivo.")
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow no está instalado.") from exc
    regularizer = tf.keras.regularizers.l2(config.architecture.l2_regularization)
    inputs = tf.keras.Input(shape=(input_dimension,), name="behavioral_features")
    value = inputs
    for index, units in enumerate(config.architecture.hidden_layers):
        value = tf.keras.layers.Dense(
            units,
            activation=config.architecture.activation,
            kernel_regularizer=regularizer,
            name=f"encoder_{index + 1}",
        )(value)
        if config.architecture.dropout:
            value = tf.keras.layers.Dropout(
                config.architecture.dropout, name=f"encoder_dropout_{index + 1}"
            )(value)
    latent = tf.keras.layers.Dense(
        config.architecture.latent_dimension,
        activation=config.architecture.activation,
        kernel_regularizer=regularizer,
        name="latent",
    )(value)
    value = latent
    for index, units in enumerate(reversed(config.architecture.hidden_layers)):
        value = tf.keras.layers.Dense(
            units,
            activation=config.architecture.activation,
            kernel_regularizer=regularizer,
            name=f"decoder_{index + 1}",
        )(value)
    outputs = tf.keras.layers.Dense(
        input_dimension,
        activation=config.architecture.output_activation,
        name="reconstruction",
    )(value)
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="behavioral_autoencoder")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.learning_rate),
        loss=config.reconstruction_loss,
    )
    return model
