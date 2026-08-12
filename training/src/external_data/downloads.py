from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.external_data.registry import (
    DatasetEntry,
    RegistryError,
    assert_download_allowed,
    load_registry,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download_registered_dataset(
    *,
    dataset_id: str,
    registry_path: str | Path,
    project_root: str | Path,
    expected_sha256: str,
    timeout_seconds: int = 120,
) -> Path:
    if len(expected_sha256) != 64:
        raise RegistryError("expected_sha256 debe ser un SHA-256 de 64 caracteres.")
    registry_file = Path(registry_path)
    registry = load_registry(registry_file)
    entry = registry.get(dataset_id)
    assert_download_allowed(entry, registry_file)
    if entry.checksum and entry.checksum.lower() != expected_sha256.lower():
        raise RegistryError("El checksum esperado no coincide con el registro aprobado.")

    raw_directory = Path(project_root) / entry.storage_path
    raw_directory.mkdir(parents=True, exist_ok=True)
    destination = raw_directory / f"{dataset_id}.download"
    if destination.exists():
        raise RegistryError(f"No se sobrescribirá el archivo raw existente: {destination}")

    request = urllib.request.Request(
        str(entry.download_url),
        headers={"User-Agent": "AndesLog-Research-Dataset-Client/1.0"},
    )
    with NamedTemporaryFile(
        prefix=f".{dataset_id}.",
        suffix=".partial",
        dir=raw_directory,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    actual = _sha256(temporary_path)
    if actual.lower() != expected_sha256.lower():
        temporary_path.unlink(missing_ok=True)
        raise RegistryError(
            f"Checksum inválido para {dataset_id}: esperado={expected_sha256}, real={actual}"
        )
    os.replace(temporary_path, destination)
    return destination


def access_instructions(entry: DatasetEntry) -> str:
    return "\n".join(
        [
            f"# Acceso a {entry.official_name}",
            "",
            f"Estado: {entry.status}",
            f"Fuente oficial: {entry.official_url}",
            "",
            *[f"{index}. {step}" for index, step in enumerate(entry.access_instructions, 1)],
            "",
            "Después de la aprobación, coloque el archivo sin modificar en:",
            f"`{entry.storage_path}`",
            "Registre su SHA-256 y no lo añada a Git.",
            "",
        ]
    )


def write_access_instructions(
    dataset_id: str, registry_path: str | Path, output_path: str | Path
) -> Path:
    entry = load_registry(registry_path).get(dataset_id)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(access_instructions(entry), encoding="utf-8")
    return target


def download_audit_record(dataset_id: str, path: Path) -> dict[str, str]:
    return {
        "dataset_id": dataset_id,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "path": path.as_posix(),
        "checksum": _sha256(path),
    }


def write_download_audit(record: dict[str, str], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return target
