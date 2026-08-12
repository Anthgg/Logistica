from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.core.exceptions import ApplicationError
from app.ml.facial_runtime import FacialRuntime

numpy = pytest.importorskip("numpy")


class FakeFace:
    def __init__(self, embedding) -> None:
        self._embedding = embedding

    @property
    def normed_embedding(self):
        return self._embedding


class FakeAnalyzer:
    def __init__(self, faces: list[FakeFace]) -> None:
        self.faces = faces

    def prepare(self, *, ctx_id: int, det_size: tuple[int, int]) -> None:
        del ctx_id, det_size

    def get(self, image: object) -> list[FakeFace]:
        assert image is not None
        return self.faces


def _image() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color=(40, 80, 120)).save(
        buffer, format="JPEG"
    )
    return buffer.getvalue()


def _runtime(
    tmp_path: Path, faces: list[FakeFace]
) -> FacialRuntime:
    templates = tmp_path / "templates"
    templates.mkdir()
    numpy.savez(
        templates / "P-0001.npz",
        template=numpy.asarray([1.0, 0.0], dtype=numpy.float32),
    )
    return FacialRuntime(
        model_name="fixture",
        model_version="facial-v1",
        model_root=tmp_path,
        templates_path=templates,
        threshold=0.5,
        device="cpu",
        analyzer=FakeAnalyzer(faces),
    )


def test_facial_runtime_normalizes_and_compares_template(
    tmp_path: Path,
) -> None:
    runtime = _runtime(
        tmp_path,
        [FakeFace(numpy.asarray([2.0, 0.0]))],
    )
    result = runtime.infer("P-0001", _image())
    assert result.similarity == pytest.approx(1.0)
    assert result.decision == "genuine"
    assert result.latency_ms >= 0


def test_facial_runtime_loads_exact_registered_nested_template(
    tmp_path: Path,
) -> None:
    template_path = (
        tmp_path
        / "templates"
        / "pilot-v0.1.0"
        / "P-0001.npz"
    )
    template_path.parent.mkdir(parents=True)
    numpy.savez(
        template_path,
        template=numpy.asarray([1.0, 0.0], dtype=numpy.float32),
    )
    runtime = FacialRuntime(
        model_name="fixture",
        model_version="facial-v1",
        model_root=tmp_path,
        templates_path=None,
        template_paths=(template_path,),
        threshold=0.5,
        device="cpu",
        analyzer=FakeAnalyzer(
            [FakeFace(numpy.asarray([1.0, 0.0], dtype=float))]
        ),
    )

    assert runtime.infer("P-0001", _image()).decision == "genuine"


@pytest.mark.parametrize(
    ("faces", "code"),
    [
        ([], "NO_FACE_DETECTED"),
        (
            [
                FakeFace(numpy.asarray([1.0, 0.0])),
                FakeFace(numpy.asarray([1.0, 0.0])),
            ],
            "MULTIPLE_FACES_DETECTED",
        ),
    ],
)
def test_facial_runtime_rejects_invalid_face_count(
    tmp_path: Path, faces: list[FakeFace], code: str
) -> None:
    runtime = _runtime(tmp_path, faces)
    with pytest.raises(ApplicationError) as error:
        runtime.infer("P-0001", _image())
    assert error.value.code == code


def test_facial_runtime_rejects_missing_template(tmp_path: Path) -> None:
    runtime = _runtime(
        tmp_path, [FakeFace(numpy.asarray([1.0, 0.0]))]
    )
    with pytest.raises(ApplicationError) as error:
        runtime.infer("P-9999", _image())
    assert error.value.code == "FACIAL_TEMPLATE_NOT_FOUND"


def test_facial_runtime_rejects_invalid_image(tmp_path: Path) -> None:
    runtime = _runtime(
        tmp_path, [FakeFace(numpy.asarray([1.0, 0.0]))]
    )
    with pytest.raises(ApplicationError) as error:
        runtime.infer("P-0001", b"not-an-image")
    assert error.value.code == "INVALID_CAPTURE"
