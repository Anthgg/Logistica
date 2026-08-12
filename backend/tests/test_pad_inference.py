from io import BytesIO

import pytest
from PIL import Image

from app.core.exceptions import ApplicationError
from app.ml.pad_runtime import PadRuntime

numpy = pytest.importorskip("numpy")


class FakePadModel:
    input_shape = (None, 32, 32, 3)

    def __init__(self, probability: float) -> None:
        self.probability = probability
        self.last_values = None

    def predict(self, values: object, *, verbose: int = 0):
        assert verbose == 0
        self.last_values = values
        return numpy.asarray([[self.probability]], dtype=float)


def _image() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 48), color=(100, 120, 140)).save(
        buffer, format="JPEG"
    )
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("probability", "decision"),
    [(0.2, "bona_fide"), (0.8, "attack")],
)
def test_pad_runtime_interprets_output_as_attack_probability(
    probability: float, decision: str
) -> None:
    model = FakePadModel(probability)
    runtime = PadRuntime(
        model=model,
        model_version="pad-v1",
        threshold=0.5,
    )
    result = runtime.infer(_image())
    assert result.attack_probability == pytest.approx(probability)
    assert result.bona_fide_probability == pytest.approx(1 - probability)
    assert result.decision == decision
    assert model.last_values.shape == (1, 32, 32, 3)


def test_pad_runtime_rejects_invalid_image() -> None:
    runtime = PadRuntime(
        model=FakePadModel(0.2),
        model_version="pad-v1",
        threshold=0.5,
    )
    with pytest.raises(ApplicationError) as error:
        runtime.infer(b"invalid")
    assert error.value.code == "INVALID_CAPTURE"


@pytest.mark.parametrize("probability", [-0.1, 1.1, float("nan")])
def test_pad_runtime_rejects_invalid_probability(
    probability: float,
) -> None:
    runtime = PadRuntime(
        model=FakePadModel(probability),
        model_version="pad-v1",
        threshold=0.5,
    )
    with pytest.raises(ApplicationError) as error:
        runtime.infer(_image())
    assert error.value.code == "INTERNAL_INFERENCE_ERROR"


def test_pad_runtime_rejects_non_image_model_shape() -> None:
    model = FakePadModel(0.2)
    model.input_shape = (None, 10)
    with pytest.raises(ApplicationError) as error:
        PadRuntime(
            model=model,
            model_version="pad-v1",
            threshold=0.5,
        )
    assert error.value.code == "MODEL_ARTIFACT_INVALID"
