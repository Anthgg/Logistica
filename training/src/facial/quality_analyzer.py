from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from src.common.config import FaceQualityConfig
from src.common.hashing import sha256_bytes
from src.common.timestamps import ensure_utc
from src.facial.image_reader import ImageReadError, read_image


class FaceQualityAnalyzer:
    def __init__(self, config: FaceQualityConfig) -> None:
        self.config = config
        cascade_path = (
            Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        )
        self.detector = cv2.CascadeClassifier(str(cascade_path))
        if self.detector.empty():
            raise RuntimeError("No fue posible cargar el detector facial de OpenCV.")

    def detect_faces(self, grayscale: np.ndarray) -> list[tuple[int, int, int, int]]:
        values = self.detector.detectMultiScale(
            grayscale,
            scaleFactor=self.config.face_detector.scale_factor,
            minNeighbors=self.config.face_detector.min_neighbors,
            minSize=self.config.face_detector.minimum_size,
        )
        return [tuple(int(part) for part in box) for box in values]

    def analyze(
        self,
        path: str | Path,
        *,
        expected_checksum: str | None,
        declared_width: int | None = None,
        declared_height: int | None = None,
        declared_file_size: int | None = None,
        visibility_state: str | None = None,
        captured_at: datetime | str | None = None,
        previous_captured_at: datetime | str | None = None,
        is_duplicate: bool = False,
        face_boxes: list[tuple[int, int, int, int]] | None = None,
    ) -> dict[str, object]:
        source = Path(path)
        reasons: list[str] = []
        result: dict[str, object] = {
            "quality_status": "rejected",
            "rejection_reasons": reasons,
            "brightness_mean": np.nan,
            "brightness_std": np.nan,
            "contrast": np.nan,
            "laplacian_variance": np.nan,
            "width": declared_width or 0,
            "height": declared_height or 0,
            "file_size": declared_file_size or 0,
            "face_count": 0,
            "face_area_ratio": 0.0,
            "duplicate_hash": expected_checksum if is_duplicate else None,
            "time_since_previous_capture": np.nan,
        }
        if not source.is_file():
            reasons.append("FILE_NOT_FOUND")
            return result
        try:
            image = read_image(source)
        except ImageReadError:
            reasons.append("UNREADABLE_IMAGE")
            return result
        result.update(
            width=image.width,
            height=image.height,
            file_size=len(image.content),
        )
        if image.image_format not in self.config.allowed_formats:
            reasons.append("UNSUPPORTED_FORMAT")
        if len(image.content) > self.config.maximum_file_size_bytes:
            reasons.append("FILE_TOO_LARGE")
        if not (
            self.config.minimum_width
            <= image.width
            <= self.config.maximum_width
            and self.config.minimum_height
            <= image.height
            <= self.config.maximum_height
        ):
            reasons.append("INVALID_DIMENSIONS")
        if (
            declared_width
            and declared_height
            and (declared_width != image.width or declared_height != image.height)
        ):
            reasons.append("INVALID_DIMENSIONS")
        actual_checksum = sha256_bytes(image.content)
        if expected_checksum and actual_checksum != expected_checksum:
            reasons.append("CHECKSUM_MISMATCH")
        if is_duplicate:
            reasons.append("DUPLICATE_CAPTURE")
        grayscale = cv2.cvtColor(image.bgr, cv2.COLOR_BGR2GRAY)
        brightness_mean = float(np.mean(grayscale))
        brightness_std = float(np.std(grayscale))
        contrast = brightness_std
        laplacian_variance = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
        result.update(
            brightness_mean=brightness_mean,
            brightness_std=brightness_std,
            contrast=contrast,
            laplacian_variance=laplacian_variance,
        )
        if brightness_mean < self.config.minimum_brightness_mean:
            reasons.append("TOO_DARK")
        if brightness_mean > self.config.maximum_brightness_mean:
            reasons.append("TOO_BRIGHT")
        if contrast < self.config.minimum_contrast:
            reasons.append("LOW_CONTRAST")
        if laplacian_variance < self.config.minimum_laplacian_variance:
            reasons.append("BLURRED_IMAGE")
        boxes = face_boxes if face_boxes is not None else self.detect_faces(grayscale)
        result["face_count"] = len(boxes)
        if not boxes:
            reasons.append("NO_FACE_DETECTED")
        elif len(boxes) > 1:
            reasons.append("MULTIPLE_FACES_DETECTED")
        if boxes:
            largest = max(boxes, key=lambda box: box[2] * box[3])
            x, y, width, height = largest
            area_ratio = float((width * height) / (image.width * image.height))
            result["face_area_ratio"] = area_ratio
            if area_ratio < self.config.minimum_face_area_ratio:
                reasons.append("FACE_TOO_SMALL")
            horizontal_margin = image.width * self.config.face_border_margin_ratio
            vertical_margin = image.height * self.config.face_border_margin_ratio
            if (
                x <= horizontal_margin
                or y <= vertical_margin
                or x + width >= image.width - horizontal_margin
                or y + height >= image.height - vertical_margin
            ):
                reasons.append("FACE_NEAR_BORDER")
        if self.config.reject_hidden_tab and visibility_state == "hidden":
            reasons.append("HIDDEN_TAB_CAPTURE")
        if captured_at and previous_captured_at:
            try:
                interval = (
                    ensure_utc(captured_at) - ensure_utc(previous_captured_at)
                ).total_seconds()
                result["time_since_previous_capture"] = float(interval)
                if interval < self.config.minimum_capture_interval_seconds:
                    reasons.append("INVALID_TIMESTAMP")
            except ValueError:
                reasons.append("INVALID_TIMESTAMP")
        elif captured_at:
            try:
                ensure_utc(captured_at)
            except ValueError:
                reasons.append("INVALID_TIMESTAMP")
        result["rejection_reasons"] = sorted(set(reasons))
        result["quality_status"] = "accepted" if not reasons else "rejected"
        return result


def quality_frame(records: list[dict[str, object]]) -> "pd.DataFrame":
    import pandas as pd

    return pd.DataFrame(records)
