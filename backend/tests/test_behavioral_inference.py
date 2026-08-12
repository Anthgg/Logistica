import pytest

from app.core.exceptions import ApplicationError
from app.ml.behavioral_runtime import BehavioralRuntime, FeatureSchema

numpy = pytest.importorskip("numpy")


class FakeScaler:
    def __init__(self) -> None:
        self.transform_calls = 0
        self.fit_calls = 0

    def transform(self, values: object):
        self.transform_calls += 1
        return numpy.asarray(values, dtype=float) * 2

    def fit(self, values: object) -> None:
        del values
        self.fit_calls += 1


class FakeAutoencoder:
    input_shape = (None, 2)

    def predict(self, values: object, *, verbose: int = 0):
        assert verbose == 0
        return numpy.zeros_like(values, dtype=float)


def _runtime() -> tuple[BehavioralRuntime, FakeScaler]:
    schema = FeatureSchema.model_validate(
        {
            "version": "v1",
            "dataset_version": "pilot-v0.1.0",
            "feature_count": 2,
            "features": [
                {
                    "name": "first",
                    "position": 0,
                    "dtype": "float64",
                    "allowed": "finite",
                },
                {
                    "name": "second",
                    "position": 1,
                    "dtype": "float64",
                    "allowed": "finite",
                },
            ],
            "checksum": "0" * 64,
        }
    )
    scaler = FakeScaler()
    return (
        BehavioralRuntime(
            model=FakeAutoencoder(),
            scaler=scaler,
            schema=schema,
            threshold=5,
            model_version="behavior-v1",
        ),
        scaler,
    )


def test_behavioral_runtime_preserves_order_and_never_fits_scaler() -> None:
    runtime, scaler = _runtime()
    result = runtime.infer({"second": 2.0, "first": 1.0})
    assert result.reconstruction_error == pytest.approx(10.0)
    assert result.decision == "anomalous"
    assert scaler.transform_calls == 1
    assert scaler.fit_calls == 0


@pytest.mark.parametrize(
    "values",
    [
        {"first": 1.0},
        {"first": 1.0, "second": float("nan")},
        {"first": 1.0, "second": float("inf")},
    ],
)
def test_behavioral_runtime_rejects_schema_or_non_finite_values(
    values: dict[str, float],
) -> None:
    runtime, _ = _runtime()
    with pytest.raises(ApplicationError) as error:
        runtime.infer(values)
    assert error.value.code == "FEATURE_SCHEMA_MISMATCH"
