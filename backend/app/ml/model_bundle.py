from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.ml.registry import RegistryModelRecord


@dataclass(frozen=True, slots=True)
class ValidatedArtifact:
    role: str
    path: Path
    checksum: str


@dataclass(frozen=True, slots=True)
class ValidatedModelRecord:
    record: RegistryModelRecord
    artifacts: tuple[ValidatedArtifact, ...]

    def artifact_named(self, name: str) -> Path | None:
        for artifact in self.artifacts:
            if artifact.path.name == name or artifact.role == name:
                return artifact.path
        return None


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    models: tuple[ValidatedModelRecord, ...]
    dataset_version: str
    loaded_at: datetime
    checksum_valid: bool

    def family(self, name: str) -> tuple[ValidatedModelRecord, ...]:
        return tuple(
            item for item in self.models if item.record.model_family == name
        )


@dataclass(slots=True)
class ComponentRuntimeStatus:
    available: bool = False
    loaded: bool = False
    checksum_valid: bool = False
    version: str | None = None
    reason_code: str | None = None


@dataclass(slots=True)
class LoaderStatus:
    global_status: str = "not_loaded"
    device: str = "cpu"
    loaded_at: datetime | None = None
    registry_checksum_valid: bool = False
    fusion_loaded: bool = False
    normalization_loaded: bool = False
    facial: ComponentRuntimeStatus = field(
        default_factory=ComponentRuntimeStatus
    )
    pad: ComponentRuntimeStatus = field(
        default_factory=ComponentRuntimeStatus
    )
    behavioral_available: int = 0
    behavioral_loaded: int = 0
    behavioral_versions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ComponentInference:
    available: bool
    valid: bool
    score: float | None
    risk: float | None
    decision: str
    latency_ms: float
    model_version: str | None
    reason_code: str | None = None
    latency_breakdown: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FusedRisk:
    risk: float
    available_components: tuple[str, ...]
    strategy: str
    latency_ms: float
