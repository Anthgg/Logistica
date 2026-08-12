import numpy as np
import pytest

from src.behavioral.autoencoder_model import build_autoencoder
from src.behavioral.trainer import reconstruction_errors


def test_autoencoder_preserves_feature_dimension(training_config) -> None:
    pytest.importorskip("tensorflow")
    config = training_config.behavioral.model_copy(
        update={
            "architecture": training_config.behavioral.architecture.model_copy(
                update={"hidden_layers": [4], "latent_dimension": 2}
            )
        }
    )
    model = build_autoencoder(6, config)
    assert model.input_shape == (None, 6)
    assert model.output_shape == (None, 6)
    matrix = np.zeros((2, 6), dtype=np.float32)
    mse, mae = reconstruction_errors(model, matrix)
    assert mse.shape == (2,)
    assert mae.shape == (2,)
