from pathlib import Path

import numpy as np
from PIL import Image

from src.common.hashing import directory_fingerprint, sha256_file
from src.facial.duplicate_detector import DuplicateDetector
from src.facial.quality_analyzer import FaceQualityAnalyzer


def _image(path: Path, pixels: np.ndarray) -> Path:
    Image.fromarray(pixels.astype(np.uint8), mode="RGB").save(path, format="JPEG")
    return path


def _accepted_image(tmp_path: Path) -> Path:
    generator = np.random.default_rng(7)
    return _image(
        tmp_path / "face.jpg",
        generator.integers(20, 235, (128, 128, 3), dtype=np.uint8),
    )


def test_raw_is_not_modified_by_analysis(tmp_path, config):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    source = _accepted_image(raw)
    before = directory_fingerprint(raw)
    FaceQualityAnalyzer(config.face_quality).analyze(
        source,
        expected_checksum=sha256_file(source),
        face_boxes=[(32, 32, 64, 64)],
    )
    assert directory_fingerprint(raw) == before


def test_readable_image_is_accepted(tmp_path, config):
    source = _accepted_image(tmp_path)
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source,
        expected_checksum=sha256_file(source),
        face_boxes=[(32, 32, 64, 64)],
    )
    assert result["quality_status"] == "accepted"


def test_corrupt_image_is_rejected(tmp_path, config):
    source = tmp_path / "broken.jpg"
    source.write_bytes(b"not-an-image")
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source, expected_checksum=None
    )
    assert "UNREADABLE_IMAGE" in result["rejection_reasons"]


def test_dark_image_is_marked(tmp_path, config):
    source = _image(tmp_path / "dark.jpg", np.zeros((128, 128, 3)))
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source, expected_checksum=sha256_file(source), face_boxes=[(32, 32, 64, 64)]
    )
    assert "TOO_DARK" in result["rejection_reasons"]


def test_blurred_image_is_marked(tmp_path, config):
    source = _image(tmp_path / "blur.jpg", np.full((128, 128, 3), 128))
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source, expected_checksum=sha256_file(source), face_boxes=[(32, 32, 64, 64)]
    )
    assert "BLURRED_IMAGE" in result["rejection_reasons"]


def test_duplicate_detector_uses_hash():
    detector = DuplicateDetector()
    assert detector.add("one", "same-hash") is False
    assert detector.add("two", "same-hash") is True
    assert detector.duplicate_groups()["same-hash"] == ["one", "two"]


def test_multiple_faces_are_detected(tmp_path, config):
    source = _accepted_image(tmp_path)
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source,
        expected_checksum=sha256_file(source),
        face_boxes=[(10, 10, 40, 40), (70, 70, 40, 40)],
    )
    assert "MULTIPLE_FACES_DETECTED" in result["rejection_reasons"]


def test_multiple_rejection_reasons_are_preserved(tmp_path, config):
    source = _image(tmp_path / "bad.jpg", np.zeros((32, 32, 3)))
    result = FaceQualityAnalyzer(config.face_quality).analyze(
        source, expected_checksum="incorrect", face_boxes=[]
    )
    assert {"INVALID_DIMENSIONS", "CHECKSUM_MISMATCH", "TOO_DARK"} <= set(
        result["rejection_reasons"]
    )
