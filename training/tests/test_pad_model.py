import pytest

from src.pad.mobilenet_model import build_mobilenetv2, unfreeze_last_layers


def test_builds_frozen_mobilenet_and_unfreezes_tail(training_config) -> None:
    pytest.importorskip("tensorflow")
    config = training_config.pad.model_copy(
        update={
            "imagenet_weights": False,
            "dense_units": 8,
            "fine_tune_last_layers": 3,
        }
    )
    model, backbone = build_mobilenetv2(config)
    assert model.output_shape == (None, 1)
    assert backbone.trainable is False
    unfreeze_last_layers(backbone, 3)
    assert any(layer.trainable for layer in backbone.layers[-3:])
    assert all(not layer.trainable for layer in backbone.layers[:-3])
