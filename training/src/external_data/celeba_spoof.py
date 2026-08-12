"""Adaptador del dataset CelebA-Spoof al esquema PAD de la Fase 7.5.

Lee la estructura real de carpetas:

    Data/{split}/{subject_id}/{live|spoof}/{image_id}.png
    Data/{split}/{subject_id}/{live|spoof}/{image_id}_BB.txt

Y produce registros compatibles con ``PAD_MANIFEST_COLUMNS`` respetando:
- ``presentation_label`` derivada de la carpeta ``live``/``spoof``.
- ``attack_type`` inferido del subdirectorio de spoof (cuando existe) o ``none``.
- Splits preservados por sujeto (sin mezclar sujetos entre particiones).
- Checksum SHA-256 por imagen.
- Sin imágenes originales en el manifiesto; solo rutas relativas.

El dataset CelebA-Spoof es **solo para investigación no comercial**.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.common.hashing import sha256_file

CELEBA_SPOOF_SPLITS = {"train", "validation", "test"}

# Mapeo de subdirectorios de spoof a attack_type del esquema PAD.
# CelebA-Spoof organiza spoof por tipo en subcarpetas; cuando no hay
# subcarpeta (estructura plana live/spoof), se usa "other".
SPOOF_SUBDIR_TO_ATTACK_TYPE: dict[str, str] = {
    "printed_photo": "printed_photo",
    "print": "printed_photo",
    "photo": "printed_photo",
    "poster": "printed_photo",
    "a4": "printed_photo",
    "cut_photo": "cut_photo",
    "screen_photo": "screen_photo",
    "pc": "screen_photo",
    "pad": "screen_photo",
    "phone": "screen_photo",
    "replayed_video": "replayed_video",
    "mask": "mask",
    "face_mask": "mask",
    "upper_body_mask": "mask",
    "region_mask": "mask",
    "3d_mask": "mask",
    "makeup": "makeup",
}


def _infer_attack_type(spoof_subdir: str | None) -> str:
    if spoof_subdir is None:
        return "other"
    key = spoof_subdir.strip().casefold()
    return SPOOF_SUBDIR_TO_ATTACK_TYPE.get(key, "other")


def _read_bb_file(bb_path: Path) -> tuple[int, int, int, int, float] | None:
    if not bb_path.is_file():
        return None
    try:
        content = bb_path.read_text(encoding="utf-8").strip()
        parts = content.split()
        if len(parts) < 5:
            return None
        return (
            int(float(parts[0])),
            int(float(parts[1])),
            int(float(parts[2])),
            int(float(parts[3])),
            float(parts[4]),
        )
    except (ValueError, OSError):
        return None


def discover_celeba_spoof_images(
    data_root: Path,
    *,
    split: str,
) -> list[Path]:
    """Descubre todas las imágenes PNG de un split de CelebA-Spoof."""
    if split not in CELEBA_SPOOF_SPLITS:
        raise ValueError(f"Split CelebA-Spoof inválido: {split}")
    split_dir = data_root / split
    if not split_dir.is_dir():
        return []
    return sorted(split_dir.rglob("*.png"))


def build_celeba_spoof_pad_records(
    data_root: str | Path,
    *,
    source_dataset: str = "celeba_spoof",
    dataset_version: str = "2020",
    license_status: str = "agreement_required",
    splits: tuple[str, ...] = ("test",),
    max_images_per_split: int | None = None,
) -> pd.DataFrame:
    """Construye registros PAD desde la estructura de carpetas de CelebA-Spoof.

    Parámetros:
        data_root: raíz del dataset (carpeta ``Data``).
        source_dataset: identificador del dataset en el registro.
        dataset_version: versión del dataset.
        license_status: estado de licencia registrado.
        splits: splits a incluir.
        max_images_per_split: límite opcional de imágenes por split
            (para pruebas rápidas o entornos con poca memoria).

    Retorna:
        DataFrame con columnas de ``PAD_MANIFEST_COLUMNS``.
    """
    root = Path(data_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"No existe el directorio: {root}")

    rows: list[dict[str, object]] = []
    for split in splits:
        if split not in CELEBA_SPOOF_SPLITS:
            raise ValueError(f"Split inválido: {split}")
        images = discover_celeba_spoof_images(root, split=split)
        if max_images_per_split is not None:
            images = images[:max_images_per_split]
        for image_path in images:
            relative = image_path.relative_to(root)
            parts = relative.parts
            # parts = (split, subject_id, [live|spoof|spoof_subdir], image.png)
            if len(parts) < 4:
                continue
            subject_id = parts[1]
            label_folder = parts[2]
            is_live = label_folder.casefold() == "live"
            is_spoof = label_folder.casefold() == "spoof"
            spoof_subdir = None
            if not is_live and not is_spoof:
                # Estructura con subcarpeta de tipo de spoof
                # parts = (split, subject_id, spoof_type, image.png)
                if len(parts) >= 4:
                    spoof_subdir = label_folder
                    is_spoof = True
            if not is_live and not is_spoof:
                continue

            image_id = image_path.stem
            bb_path = image_path.with_name(f"{image_id}_BB.txt")
            bb = _read_bb_file(bb_path)
            # Saltar imágenes truncadas (archivos muy pequeños o sin datos)
            if image_path.stat().st_size < 256:
                continue
            checksum = sha256_file(image_path)
            session_id = f"{subject_id}-{split}"
            video_id = f"{subject_id}-{image_id}"

            row: dict[str, object] = {
                "dataset_version": dataset_version,
                "source_dataset": source_dataset,
                "source_subject_id": subject_id,
                "source_session_id": session_id,
                "source_video_id": video_id,
                "source_capture_id": image_id,
                "file_path": relative.as_posix(),
                "checksum": checksum,
                "presentation_label": "bona_fide" if is_live else "attack",
                "attack_type": "none" if is_live else _infer_attack_type(spoof_subdir),
                "capture_device": None,
                "presentation_device": None,
                "illumination": None,
                "environment": None,
                "split_original": split,
                "split_project": split,
                "quality_status": "accepted",
                "rejection_reasons": [],
                "license_status": license_status,
            }
            if bb is not None:
                row["capture_device"] = "celeba_spoof_sensor"
            rows.append(row)

    if not rows:
        raise ValueError(
            "No se encontraron imágenes CelebA-Spoof en los splits solicitados."
        )
    return pd.DataFrame(rows)


def assign_subject_disjoint_splits(
    records: pd.DataFrame,
    *,
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Reasigna ``split_project`` garantizando que sujetos no crucen particiones.

    Útil cuando el dataset solo trae un split (ej. ``test``) y necesitamos
    crear train/validation/test disjuntos por sujeto para experimentación.
    """
    if "source_subject_id" not in records.columns:
        raise ValueError("Falta source_subject_id.")
    subjects = sorted(records["source_subject_id"].dropna().unique())
    if len(subjects) < 3:
        raise ValueError(
            "Se necesitan al menos 3 sujetos para dividir por sujeto."
        )
    rng = __import__("numpy").random.default_rng(random_seed)
    rng.shuffle(subjects)
    n = len(subjects)
    n_train = max(1, int(n * train_ratio))
    n_validation = max(1, int(n * validation_ratio))
    train_subjects = set(subjects[:n_train])
    validation_subjects = set(subjects[n_train : n_train + n_validation])
    test_subjects = set(subjects[n_train + n_validation :])

    def assign(subject: object) -> str:
        s = str(subject)
        if s in train_subjects:
            return "train"
        if s in validation_subjects:
            return "validation"
        return "test"

    result = records.copy()
    result["split_project"] = result["source_subject_id"].map(assign)
    return result