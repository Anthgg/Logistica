import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AcceptedModelStatus = Literal["candidate", "approved_for_integration"]
KnownModelStatus = Literal[
    "experimental",
    "candidate",
    "approved_for_integration",
    "rejected",
    "failed",
    "incomplete",
    "missing",
]
ModelFamily = Literal["facial", "pad", "behavioral"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_checksum(payload: dict[str, object]) -> str:
    serializable = {
        key: value for key, value in payload.items() if key != "checksum"
    }
    encoded = json.dumps(
        serializable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: str | None = None


class RegistryModelRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model_family: ModelFamily
    model_name: str | None = None
    model_type: str | None = None
    model_version: str = Field(min_length=1)
    participant_id: str | None = None
    dataset_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    status: KnownModelStatus
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    artifact_checksums: dict[str, str] = Field(default_factory=dict)
    feature_schema_checksum: str | None = None
    threshold_path: str | None = None
    threshold_checksum: str | None = None
    test_rows_used: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    registered_at: datetime | None = None

    @model_validator(mode="after")
    def validate_participant_scope(self) -> "RegistryModelRecord":
        if self.model_family == "behavioral" and not self.participant_id:
            raise ValueError(
                "Un modelo conductual requiere participant_id seudonimizado."
            )
        missing_checksums = set(self.artifact_paths) - set(
            self.artifact_checksums
        )
        if missing_checksums:
            raise ValueError(
                "Cada artifact_path requiere un artifact_checksum."
            )
        if bool(self.threshold_path) != bool(self.threshold_checksum):
            raise ValueError(
                "threshold_path y threshold_checksum deben declararse juntos."
            )
        checksum_values = [
            *self.artifact_checksums.values(),
            *(
                [self.feature_schema_checksum]
                if self.feature_schema_checksum
                else []
            ),
            *(
                [self.threshold_checksum]
                if self.threshold_checksum
                else []
            ),
        ]
        if any(
            re.fullmatch(r"[0-9a-f]{64}", checksum) is None
            for checksum in checksum_values
        ):
            raise ValueError("Un checksum registrado no es SHA-256 válido.")
        return self

    def artifact_references(self) -> list[ArtifactReference]:
        references = list(self.artifacts)
        known_paths = {reference.path for reference in references}
        for role, path in self.artifact_paths.items():
            if path in known_paths:
                continue
            checksum = self.artifact_checksums.get(role)
            if checksum:
                references.append(
                    ArtifactReference(path=path, sha256=checksum, role=role)
                )
                known_paths.add(path)
        if (
            self.threshold_path
            and self.threshold_checksum
            and self.threshold_path not in known_paths
        ):
            references.append(
                ArtifactReference(
                    path=self.threshold_path,
                    sha256=self.threshold_checksum,
                    role="threshold",
                )
            )
        return references


class ModelRegistryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(min_length=1)
    models: list[RegistryModelRecord]
