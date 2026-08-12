from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import PadTrainingConfig
from src.pad.mobilenet_model import compile_pad_model, unfreeze_last_layers


@dataclass(frozen=True)
class PadTrainingResult:
    best_model_path: Path
    frozen_checkpoint: Path
    finetuned_checkpoint: Path
    history_path: Path
    best_epoch: int


def _callbacks(path: Path, config: PadTrainingConfig) -> list[Any]:
    import tensorflow as tf

    return [
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
            filepath=str(path),
            monitor="val_loss",
            save_best_only=True,
        ),
    ]


def _history_frame(history: Any, phase: str, epoch_offset: int = 0) -> pd.DataFrame:
    frame = pd.DataFrame(history.history)
    frame.insert(0, "epoch", range(epoch_offset + 1, epoch_offset + len(frame) + 1))
    frame.insert(1, "phase", phase)
    return frame


def train_pad(
    model: Any,
    backbone: Any,
    train_dataset: Any,
    validation_dataset: Any,
    *,
    config: PadTrainingConfig,
    checkpoint_dir: Path,
    class_weight: dict[int, float] | None,
    resume: bool = False,
) -> PadTrainingResult:
    import tensorflow as tf

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    frozen_path = checkpoint_dir / "best_frozen.keras"
    finetuned_path = checkpoint_dir / "best_finetuned.keras"
    if resume and finetuned_path.is_file():
        model = tf.keras.models.load_model(finetuned_path)
        history_path = checkpoint_dir / "training_history.csv"
        history = pd.read_csv(history_path) if history_path.is_file() else pd.DataFrame()
        return PadTrainingResult(
            best_model_path=finetuned_path,
            frozen_checkpoint=frozen_path,
            finetuned_checkpoint=finetuned_path,
            history_path=history_path,
            best_epoch=int(history.loc[history["val_loss"].idxmin(), "epoch"])
            if not history.empty
            else 0,
        )
    compile_pad_model(model, config.learning_rate_frozen, config.label_smoothing)
    frozen_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=config.epochs_frozen,
        callbacks=_callbacks(frozen_path, config),
        class_weight=class_weight,
        verbose=2,
    )
    if frozen_path.is_file():
        model = tf.keras.models.load_model(frozen_path)
        backbone = next(
            layer
            for layer in model.layers
            if isinstance(layer, tf.keras.Model)
            and layer.name.startswith("mobilenetv2")
        )
    unfreeze_last_layers(backbone, config.fine_tune_last_layers)
    compile_pad_model(model, config.learning_rate_finetuning, config.label_smoothing)
    finetuned_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=config.epochs_finetuning,
        callbacks=_callbacks(finetuned_path, config),
        class_weight=class_weight,
        verbose=2,
    )
    history = pd.concat(
        [
            _history_frame(frozen_history, "frozen"),
            _history_frame(
                finetuned_history, "finetuning", len(frozen_history.history["loss"])
            ),
        ],
        ignore_index=True,
    )
    history_path = checkpoint_dir / "training_history.csv"
    history.to_csv(history_path, index=False)
    best_path = finetuned_path if finetuned_path.is_file() else frozen_path
    return PadTrainingResult(
        best_model_path=best_path,
        frozen_checkpoint=frozen_path,
        finetuned_checkpoint=finetuned_path,
        history_path=history_path,
        best_epoch=int(history.loc[history["val_loss"].idxmin(), "epoch"]),
    )
