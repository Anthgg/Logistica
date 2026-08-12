import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from src.behavioral.event_loader import capture_file_path
from src.common.hashing import sha256_file
from src.common.timestamps import iso_utc, utc_now


class RawExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class FacialRawExportResult:
    bucket: str
    discovered: int
    exported: int
    already_present: int
    dry_run: bool
    report_path: Path


def gcloud_download(bucket: str, object_name: str, target: Path) -> None:
    executable = shutil.which("gcloud")
    if not executable:
        raise RawExportError("gcloud CLI no está disponible en PATH.")
    result = subprocess.run(
        [
            executable,
            "storage",
            "cp",
            f"gs://{bucket}/{object_name}",
            str(target),
            "--quiet",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RawExportError(
            f"No fue posible exportar el objeto asociado a {object_name}."
        )


def export_facial_raw(
    captures: pd.DataFrame,
    *,
    bucket: str,
    raw_root: Path,
    staging_root: Path,
    report_path: Path,
    dry_run: bool = False,
    downloader: Callable[[str, str, Path], None] = gcloud_download,
) -> FacialRawExportResult:
    if not bucket.strip():
        raise ValueError("El bucket de capturas es obligatorio.")
    required = {"capture_id", "storage_path", "checksum"}
    missing = required - set(captures.columns)
    if missing and not captures.empty:
        raise ValueError(
            "Faltan columnas de captura: " + ", ".join(sorted(missing))
        )
    exported = 0
    already_present = 0
    seen_paths: set[str] = set()
    records: list[dict[str, object]] = []
    ordered = (
        captures.sort_values(
            [
                column
                for column in ("session_id", "sequence_number", "capture_id")
                if column in captures
            ],
            kind="stable",
        )
        if not captures.empty
        else captures
    )
    for capture in ordered.to_dict(orient="records"):
        capture_id = str(capture["capture_id"])
        object_name = str(capture["storage_path"])
        checksum = str(capture["checksum"] or "").lower()
        if not checksum or len(checksum) != 64:
            raise RawExportError(f"Checksum inválido para capture_id={capture_id}.")
        if object_name in seen_paths:
            raise RawExportError(f"storage_path duplicado: {object_name}.")
        seen_paths.add(object_name)
        try:
            target = capture_file_path(raw_root, object_name)
        except ValueError as exc:
            raise RawExportError(
                f"storage_path inseguro para capture_id={capture_id}."
            ) from exc
        status = "planned"
        if target.exists():
            if sha256_file(target) != checksum:
                raise RawExportError(
                    f"El archivo raw existente no coincide: capture_id={capture_id}."
                )
            already_present += 1
            status = "already_present"
        elif not dry_run:
            staging_root.mkdir(parents=True, exist_ok=True)
            staging = staging_root / f"{capture_id}.part"
            if staging.exists():
                staging.unlink()
            try:
                downloader(bucket, object_name, staging)
                if not staging.is_file():
                    raise RawExportError(
                        f"El objeto no produjo archivo: capture_id={capture_id}."
                    )
                if sha256_file(staging) != checksum:
                    raise RawExportError(
                        f"Checksum remoto inválido: capture_id={capture_id}."
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise RawExportError(
                        f"El destino apareció durante la exportación: {object_name}."
                    )
                staging.replace(target)
            finally:
                if staging.exists():
                    staging.unlink()
            exported += 1
            status = "exported"
        records.append(
            {
                "capture_id": capture_id,
                "storage_path": object_name,
                "checksum": checksum,
                "status": status,
            }
        )
    result = FacialRawExportResult(
        bucket=bucket,
        discovered=len(captures),
        exported=exported,
        already_present=already_present,
        dry_run=dry_run,
        report_path=report_path,
    )
    if not dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    **asdict(result),
                    "report_path": report_path.as_posix(),
                    "generated_at": iso_utc(utc_now()),
                    "records": records,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
    return result
