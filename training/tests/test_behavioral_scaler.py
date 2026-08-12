import numpy as np

from src.behavioral.scaler import (
    fit_participant_scaler,
    load_scaler,
    save_scaler,
)


def test_scaler_uses_only_supplied_train_and_roundtrips(tmp_path) -> None:
    train = np.array([[1.0, 10.0], [3.0, 30.0]])
    scaler = fit_participant_scaler(train)
    assert scaler.mean_.tolist() == [2.0, 20.0]
    path = tmp_path / "scaler.joblib"
    checksum = save_scaler(scaler, path)
    assert len(checksum) == 64
    restored = load_scaler(path)
    assert np.allclose(restored.transform(train), scaler.transform(train))
