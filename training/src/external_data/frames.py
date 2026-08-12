from __future__ import annotations

from pathlib import Path

import cv2
import pandas as pd

from src.common.hashing import sha256_file

VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}


def validate_frames_per_second(value: float) -> float:
    fps = float(value)
    if not 1.0 <= fps <= 5.0:
        raise ValueError("frames_per_second debe estar entre 1 y 5.")
    return fps


def extract_video_frames(
    *,
    video_path: str | Path,
    raw_root: str | Path,
    output_root: str | Path,
    source_dataset: str,
    source_video_id: str,
    frames_per_second: float = 2.0,
) -> pd.DataFrame:
    sample_rate = validate_frames_per_second(frames_per_second)
    video = Path(video_path).resolve()
    raw = Path(raw_root).resolve()
    output = Path(output_root).resolve()
    video.relative_to(raw)
    try:
        output.relative_to(raw)
    except ValueError:
        pass
    else:
        raise ValueError("Los frames derivados no pueden escribirse dentro de raw.")
    if video.suffix.casefold() not in VIDEO_EXTENSIONS:
        raise ValueError(f"Formato de video no permitido: {video.suffix}")

    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video}")
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if source_fps <= 0:
        capture.release()
        raise ValueError(f"FPS de origen inválido: {video}")
    step = max(1, round(source_fps / sample_rate))
    target_dir = output / source_dataset / source_video_id
    target_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    seen_checksums: set[str] = set()
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % step == 0:
            timestamp_ms = float(capture.get(cv2.CAP_PROP_POS_MSEC))
            target = target_dir / f"{frame_index:09d}.jpg"
            if target.exists():
                capture.release()
                raise ValueError(f"No se sobrescribirá el frame existente: {target}")
            if not cv2.imwrite(str(target), frame):
                capture.release()
                raise OSError(f"No se pudo escribir el frame: {target}")
            checksum = sha256_file(target)
            rows.append(
                {
                    "source_dataset": source_dataset,
                    "source_video_id": source_video_id,
                    "source_video_path": video.relative_to(raw).as_posix(),
                    "frame_index": frame_index,
                    "timestamp_ms": timestamp_ms,
                    "file_path": target.relative_to(output.parents[1]).as_posix(),
                    "checksum": checksum,
                    "is_duplicate": checksum in seen_checksums,
                }
            )
            seen_checksums.add(checksum)
        frame_index += 1
    capture.release()
    return pd.DataFrame(rows)


def discover_videos(raw_dataset_path: str | Path) -> list[Path]:
    root = Path(raw_dataset_path)
    return sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and item.suffix.casefold() in VIDEO_EXTENSIONS
    )
