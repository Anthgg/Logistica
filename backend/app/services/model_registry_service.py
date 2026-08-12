import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.exceptions import ApplicationError
from app.core.model_settings import (
    PROJECT_ROOT,
    ResolvedModelSettings,
)
from app.ml.model_bundle import (
    RegistrySnapshot,
    ValidatedArtifact,
    ValidatedModelRecord,
)
from app.ml.registry import (
    ModelRegistryDocument,
    RegistryModelRecord,
    sha256_file,
)

ACCEPTED_STATUSES = {"candidate", "approved_for_integration"}


class ModelRegistryService:
    def __init__(
        self,
        source_settings: Settings = settings,
        *,
        registry_path: Path | None = None,
        artifact_root: Path | None = None,
    ) -> None:
        self.settings = source_settings
        resolved = ResolvedModelSettings.from_settings(source_settings)
        self.registry_path = registry_path or resolved.registry_path
        self.artifact_root = (artifact_root or PROJECT_ROOT).resolve()

    def load(self) -> RegistrySnapshot:
        if not self.registry_path.is_file():
            raise ApplicationError(
                "MODEL_REGISTRY_UNAVAILABLE",
                "El registro central de modelos no está disponible.",
                503,
            )
        try:
            payload = json.loads(
                self.registry_path.read_text(encoding="utf-8")
            )
            document = ModelRegistryDocument.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ApplicationError(
                "MODEL_REGISTRY_UNAVAILABLE",
                "El registro central de modelos no es válido.",
                503,
            ) from exc
        selected = self._selected_records(document.models)
        validated = tuple(self._validate_record(record) for record in selected)
        dataset_versions = {
            item.record.dataset_version for item in validated
        }
        if len(dataset_versions) > 1:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "Los modelos seleccionados usan datasets incompatibles.",
                503,
            )
        return RegistrySnapshot(
            models=validated,
            dataset_version=next(iter(dataset_versions), ""),
            loaded_at=datetime.now(timezone.utc),
            checksum_valid=True,
        )

    def _selected_records(
        self, records: list[RegistryModelRecord]
    ) -> list[RegistryModelRecord]:
        selected: list[RegistryModelRecord] = []
        for record in records:
            version_matches = (
                record.model_family == "facial"
                and record.model_version
                == self.settings.FACIAL_MODEL_VERSION
            ) or (
                record.model_family == "pad"
                and record.model_version == self.settings.PAD_MODEL_VERSION
            ) or (
                record.model_family == "behavioral"
                and record.model_version.startswith(
                    self.settings.BEHAVIORAL_MODEL_VERSION_PREFIX
                )
            )
            if not version_matches:
                continue
            if record.status not in ACCEPTED_STATUSES:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Un modelo seleccionado no está aprobado para integración.",
                    503,
                )
            if record.test_rows_used != 0:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Un modelo seleccionado declara uso del conjunto test.",
                    503,
                )
            selected.append(record)
        return selected

    def _validate_record(
        self, record: RegistryModelRecord
    ) -> ValidatedModelRecord:
        references = record.artifact_references()
        if not references:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "Un modelo seleccionado no declara artefactos.",
                503,
            )
        artifacts: list[ValidatedArtifact] = []
        for reference in references:
            path = self._resolve_artifact(reference.path)
            if not path.is_file():
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "Falta un artefacto registrado.",
                    503,
                )
            actual = sha256_file(path)
            if actual != reference.sha256:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "El checksum de un artefacto no coincide.",
                    503,
                )
            artifacts.append(
                ValidatedArtifact(
                    role=reference.role or path.stem,
                    path=path,
                    checksum=actual,
                )
            )
        if record.feature_schema_checksum:
            schema_artifact = next(
                (
                    artifact
                    for artifact in artifacts
                    if artifact.path.name == "feature_schema.json"
                    or artifact.role == "feature_schema"
                ),
                None,
            )
            if (
                schema_artifact is None
                or schema_artifact.checksum
                != record.feature_schema_checksum
            ):
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "El checksum del esquema de características no coincide.",
                    503,
                )
        if record.threshold_checksum:
            threshold_artifact = next(
                (
                    artifact
                    for artifact in artifacts
                    if artifact.role == "threshold"
                    or "threshold" in artifact.path.name.casefold()
                    or "thresholds"
                    in {
                        part.casefold()
                        for part in artifact.path.parts
                    }
                ),
                None,
            )
            if (
                threshold_artifact is None
                or threshold_artifact.checksum
                != record.threshold_checksum
            ):
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "El checksum del umbral registrado no coincide.",
                    503,
                )
        self._validate_required_artifacts(record, artifacts)
        return ValidatedModelRecord(
            record=record,
            artifacts=tuple(artifacts),
        )

    def _resolve_artifact(self, value: str) -> Path:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El registro contiene una ruta de artefacto no permitida.",
                503,
            )
        resolved = (self.artifact_root / relative).resolve()
        try:
            resolved.relative_to(self.artifact_root)
        except ValueError as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El registro contiene una ruta fuera del proyecto.",
                503,
            ) from exc
        return resolved

    @staticmethod
    def _validate_required_artifacts(
        record: RegistryModelRecord,
        artifacts: list[ValidatedArtifact],
    ) -> None:
        names = {artifact.path.name for artifact in artifacts}
        suffixes = {artifact.path.suffix.casefold() for artifact in artifacts}
        threshold_present = any(
            "threshold" in artifact.path.name.casefold()
            or artifact.role == "threshold"
            or "thresholds"
            in {part.casefold() for part in artifact.path.parts}
            for artifact in artifacts
        )
        if record.model_family == "facial":
            complete = ".npz" in suffixes and threshold_present
        elif record.model_family == "pad":
            exported_model = any(
                artifact.path.suffix.casefold() == ".keras"
                and "exported"
                in {part.casefold() for part in artifact.path.parts}
                for artifact in artifacts
            )
            complete = exported_model and threshold_present
        else:
            complete = {
                "autoencoder.keras",
                "scaler.joblib",
                "threshold.json",
                "feature_schema.json",
                "metadata.json",
            } <= names
        if not complete:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El bundle del modelo seleccionado está incompleto.",
                503,
            )
