from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from src.common.hashing import directory_fingerprint

DatasetStatus = Literal[
    "pending_review",
    "approved",
    "agreement_required",
    "downloaded",
    "rejected",
    "unavailable",
]
Modality = Literal["pad", "keyboard", "mouse", "keyboard_mouse_touch"]


class RegistryError(RuntimeError):
    """Error de integridad del registro de datasets."""


class DatasetNotApprovedError(RegistryError):
    """El dataset no está aprobado para descarga."""


class LicenseGateError(RegistryError):
    """No existe evidencia de licencia suficiente para continuar."""


class DatasetEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(pattern=r"^[a-z0-9_]+$")
    official_name: str
    official_url: HttpUrl
    download_url: HttpUrl | None = None
    version: str | None = None
    modality: Modality
    intended_use: list[str]
    license_name: str | None = None
    license_url: HttpUrl | None = None
    license_reviewed_at: str
    license_copy_path: str | None = None
    commercial_use_allowed: bool | None = None
    derived_models_allowed: bool | None = None
    redistribution_allowed: bool | None = None
    agreement_required: bool
    agreement_evidence_path: str | None = None
    citation: str
    downloaded_at: str | None = None
    checksum: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    storage_path: str
    status: DatasetStatus
    access_instructions: list[str]
    approved_download_hosts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_download_state(self) -> "DatasetEntry":
        if self.status == "downloaded" and (not self.downloaded_at or not self.checksum):
            raise ValueError("Un dataset descargado debe registrar fecha y checksum SHA-256.")
        if (
            self.status == "approved"
            and self.download_url is None
            and not self.agreement_required
        ):
            raise ValueError(
                "Un dataset aprobado sin entrega manual necesita download_url."
            )
        return self


class DatasetRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    reviewed_at: str
    datasets: list[DatasetEntry]

    @model_validator(mode="after")
    def unique_ids(self) -> "DatasetRegistry":
        identifiers = [entry.dataset_id for entry in self.datasets]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("dataset_id debe ser único.")
        return self

    def get(self, dataset_id: str) -> DatasetEntry:
        for entry in self.datasets:
            if entry.dataset_id == dataset_id:
                return entry
        raise RegistryError(f"Dataset no registrado: {dataset_id}")


def load_registry(path: str | Path) -> DatasetRegistry:
    registry_path = Path(path)
    if not registry_path.is_file():
        raise RegistryError(f"No existe el registro: {registry_path}")
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    return DatasetRegistry.model_validate(payload)


def resolve_registry_path(registry_path: Path, relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    candidate = Path(relative_path)
    return candidate if candidate.is_absolute() else registry_path.parent.parent / candidate


def assert_license_ready(entry: DatasetEntry, registry_path: str | Path) -> None:
    path = Path(registry_path)
    license_copy = resolve_registry_path(path, entry.license_copy_path)
    if not entry.license_name or not entry.license_url or license_copy is None:
        raise LicenseGateError(f"{entry.dataset_id}: faltan metadatos o copia de licencia.")
    if not license_copy.is_file():
        raise LicenseGateError(
            f"{entry.dataset_id}: no existe la copia de licencia {license_copy}."
        )
    if entry.agreement_required:
        evidence = resolve_registry_path(path, entry.agreement_evidence_path)
        if evidence is None or not evidence.is_file():
            raise LicenseGateError(
                f"{entry.dataset_id}: requiere acuerdo aprobado; siga access_instructions."
            )


def assert_download_allowed(entry: DatasetEntry, registry_path: str | Path) -> None:
    if entry.status != "approved":
        instructions = " ".join(entry.access_instructions)
        raise DatasetNotApprovedError(
            f"{entry.dataset_id}: estado={entry.status}; descarga bloqueada. {instructions}"
        )
    assert_license_ready(entry, registry_path)
    if entry.download_url is None:
        raise RegistryError(f"{entry.dataset_id}: falta download_url oficial.")
    host = entry.download_url.host or ""
    if host not in set(entry.approved_download_hosts):
        raise RegistryError(f"{entry.dataset_id}: host de descarga no autorizado: {host}")


def verify_registry_licenses(
    registry_path: str | Path,
) -> list[dict[str, str | bool]]:
    path = Path(registry_path)
    registry = load_registry(path)
    results: list[dict[str, str | bool]] = []
    for entry in registry.datasets:
        try:
            assert_license_ready(entry, path)
        except LicenseGateError as exc:
            results.append(
                {"dataset_id": entry.dataset_id, "ready": False, "detail": str(exc)}
            )
        else:
            results.append(
                {
                    "dataset_id": entry.dataset_id,
                    "ready": True,
                    "detail": "evidencia de licencia presente",
                }
            )
    return results


def write_download_status(
    registry_path: str | Path,
    output_path: str | Path,
) -> Path:
    registry = load_registry(registry_path)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "datasets": {
            entry.dataset_id: {
                "status": entry.status,
                "downloaded_at": entry.downloaded_at,
                "checksum": entry.checksum,
                "storage_path": entry.storage_path,
            }
            for entry in registry.datasets
        },
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix=".download-status.",
        dir=target.parent,
        delete=False,
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)
    return target


def mark_dataset_downloaded(
    registry_path: str | Path,
    *,
    dataset_id: str,
    checksum: str,
    downloaded_at: str,
) -> None:
    path = Path(registry_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    found = False
    for entry in payload["datasets"]:
        if entry["dataset_id"] == dataset_id:
            entry["status"] = "downloaded"
            entry["checksum"] = checksum
            entry["downloaded_at"] = downloaded_at
            found = True
            break
    if not found:
        raise RegistryError(f"Dataset no registrado: {dataset_id}")
    DatasetRegistry.model_validate(payload)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".yaml",
        prefix=".datasets.",
        dir=path.parent,
        delete=False,
    ) as temporary:
        yaml.safe_dump(payload, temporary, allow_unicode=True, sort_keys=False)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def raw_snapshot(path: str | Path) -> dict[str, str]:
    return directory_fingerprint(path)


def assert_raw_unchanged(before: dict[str, str], path: str | Path) -> None:
    after = raw_snapshot(path)
    if before != after:
        changed = sorted(set(before) ^ set(after))
        changed.extend(
            key for key in sorted(set(before) & set(after)) if before[key] != after[key]
        )
        raise RegistryError(
            "La carpeta raw fue modificada durante el procesamiento: "
            + ", ".join(dict.fromkeys(changed))
        )
