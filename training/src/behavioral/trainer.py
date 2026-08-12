from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.common.config import BehavioralTrainingConfig


@dataclass(frozen=True)
class AutoencoderTrainingResult:
    model_path: Path
    history_path: Path
    epochs_executed: int
    best_epoch: int


def reconstruction_errors(model: Any, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    reconstructed = np.asarray(model.predict(matrix, verbose=0), dtype=np.float64)
    if reconstructed.shape != matrix.shape:
        raise ValueError("La reconstrucción no conserva la dimensión de entrada.")
    mse = np.mean(np.square(matrix - reconstructed), axis=1)
    mae = np.mean(np.abs(matrix - reconstructed), axis=1)
    return mse, mae


def train_autoencoder(
    model: Any,
    train_matrix: np.ndarray,
    *,
    config: BehavioralTrainingConfig,
    output_dir: Path,
    resume: bool = False,
) -> AutoencoderTrainingResult:
    import tensorflow as tf

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "autoencoder.keras"
    history_path = output_dir / "training_history.csv"
    if resume and model_path.is_file():
        history = pd.read_csv(history_path) if history_path.is_file() else pd.DataFrame()
        return AutoencoderTrainingResult(
            model_path=model_path,
            history_path=history_path,
            epochs_executed=int(len(history)),
            best_epoch=int(history.loc[history["val_loss"].idxmin(), "epoch"])
            if not history.empty
            else 0,
        )
    train, internal_validation = train_test_split(
        train_matrix,
        test_size=config.validation_fraction_from_train,
        random_state=config.random_seed,
        shuffle=True,
    )
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=config.early_stopping_patience,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            patience=config.reduce_lr_patience,
            factor=0.2,
            min_lr=1e-8,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(model_path),
            monitor="val_loss",
            save_best_only=True,
        ),
    ]
    history_object = model.fit(
        train,
        train,
        validation_data=(internal_validation, internal_validation),
        batch_size=min(config.batch_size, len(train)),
        epochs=config.epochs,
        callbacks=callbacks,
        verbose=2,
        shuffle=True,
    )
    history = pd.DataFrame(history_object.history)
    history.insert(0, "epoch", range(1, len(history) + 1))
    history.to_csv(history_path, index=False)
    if not model_path.is_file():
        model.save(model_path)
    return AutoencoderTrainingResult(
        model_path=model_path,
        history_path=history_path,
        epochs_executed=len(history),
        best_epoch=int(history.loc[history["val_loss"].idxmin(), "epoch"]),
    )
