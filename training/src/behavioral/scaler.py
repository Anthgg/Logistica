from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler

from src.common.hashing import sha256_file


def fit_participant_scaler(train_matrix: np.ndarray) -> StandardScaler:
    if train_matrix.ndim != 2 or train_matrix.shape[0] == 0:
        raise ValueError("El scaler requiere una matriz train bidimensional no vacía.")
    if not np.isfinite(train_matrix).all():
        raise ValueError("El scaler no acepta valores no finitos.")
    return StandardScaler().fit(train_matrix)


def save_scaler(scaler: StandardScaler, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, path)
    return sha256_file(path)


def load_scaler(path: Path) -> StandardScaler:
    scaler = joblib.load(path)
    if not isinstance(scaler, StandardScaler):
        raise TypeError("El artefacto no es un StandardScaler.")
    return scaler
