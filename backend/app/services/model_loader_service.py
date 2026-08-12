import json
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.exceptions import ApplicationError
from app.core.model_settings import ResolvedModelSettings
from app.ml.behavioral_runtime import (
    BehavioralArtifactPaths,
    BehavioralRuntime,
)
from app.ml.facial_runtime import FacialRuntime
from app.ml.fusion_runtime import FusionConfig, ScoreNormalizationConfig
from app.ml.model_bundle import (
    LoaderStatus,
    RegistrySnapshot,
    ValidatedModelRecord,
)
from app.ml.pad_runtime import PadRuntime
from app.ml.registry import canonical_checksum
from app.services.fusion_service import FusionService
from app.services.model_registry_service import ModelRegistryService
from app.services.score_normalization_service import (
    ScoreNormalizationService,
)

logger = logging.getLogger("app.models")


class ModelLoaderService:
    def __init__(self, source_settings: Settings = settings) -> None:
        self.settings = source_settings
        self.paths = ResolvedModelSettings.from_settings(source_settings)
        self.registry = ModelRegistryService(source_settings)
        self.status = LoaderStatus(device=self._select_device())
        self.snapshot: RegistrySnapshot | None = None
        self.facial_runtime: FacialRuntime | None = None
        self.pad_runtime: PadRuntime | None = None
        self.normalization: ScoreNormalizationService | None = None
        self.fusion: FusionService | None = None
        self._behavioral_records: dict[str, ValidatedModelRecord] = {}
        self._behavioral_cache: OrderedDict[
            str, BehavioralRuntime
        ] = OrderedDict()
        self._cache_lock = RLock()
        self._participant_locks: dict[str, RLock] = {}

    def startup(self) -> LoaderStatus:
        if not self.settings.MODEL_LOAD_ON_STARTUP:
            self.status.global_status = "disabled"
            return self.status
        try:
            self.snapshot = self.registry.load()
            self.status.registry_checksum_valid = True
        except ApplicationError as exc:
            self._record_error(exc.code)
            self.status.global_status = "unavailable"
            if self.settings.REQUIRE_ALL_MODELS:
                raise
            return self.status
        self._catalog_behavioral()
        self._load_normalization_and_fusion()
        self._load_facial()
        self._load_pad()
        if self.settings.BEHAVIORAL_MODEL_LOADING_MODE == "eager":
            for participant_code in sorted(self._behavioral_records):
                try:
                    self.get_behavioral_runtime(participant_code)
                except ApplicationError as exc:
                    self._record_error(exc.code)
                    if self.settings.REQUIRE_ALL_MODELS:
                        raise
        self.status.loaded_at = datetime.now(timezone.utc)
        required_ready = (
            self.facial_runtime is not None
            and self.pad_runtime is not None
            and self.normalization is not None
            and self.fusion is not None
        )
        self.status.global_status = "ready" if required_ready else "degraded"
        if self.settings.REQUIRE_ALL_MODELS and not required_ready:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "No fue posible cargar todos los modelos obligatorios.",
                503,
            )
        logger.info(
            "Model runtime initialized | status=%s | device=%s",
            self.status.global_status,
            self.status.device,
        )
        return self.status

    def shutdown(self) -> None:
        with self._cache_lock:
            self._behavioral_cache.clear()
            self._participant_locks.clear()

    def has_behavioral_model(self, participant_code: str) -> bool:
        return participant_code in self._behavioral_records

    def _select_device(self) -> str:
        if self.settings.MODEL_DEVICE in {"cpu", "gpu"}:
            return self.settings.MODEL_DEVICE
        try:
            import onnxruntime

            if "CUDAExecutionProvider" in onnxruntime.get_available_providers():
                return "gpu"
        except Exception:
            pass
        return "cpu"

    def _record_error(self, code: str) -> None:
        if code not in self.status.errors:
            self.status.errors.append(code)

    def _catalog_behavioral(self) -> None:
        if self.snapshot is None:
            return
        self._behavioral_records = {
            item.record.participant_id: item
            for item in self.snapshot.family("behavioral")
            if item.record.participant_id is not None
        }
        self.status.behavioral_available = len(self._behavioral_records)
        self.status.behavioral_versions = sorted(
            {
                item.record.model_version
                for item in self._behavioral_records.values()
            }
        )

    def _load_normalization_and_fusion(self) -> None:
        if self.snapshot is None:
            return
        try:
            normalization = self._read_checked_config(
                self.paths.normalization_config_path,
                ScoreNormalizationConfig,
            )
            fusion = self._read_checked_config(
                self.paths.fusion_config_path,
                FusionConfig,
            )
            if self.snapshot.dataset_version and (
                normalization.dataset_version
                != self.snapshot.dataset_version
                or fusion.dataset_version != self.snapshot.dataset_version
            ):
                raise ApplicationError(
                    "FUSION_CONFIG_UNAVAILABLE",
                    "La fusión y los modelos usan datasets incompatibles.",
                    503,
                )
            self.normalization = ScoreNormalizationService(normalization)
            self.fusion = FusionService(fusion)
            self.status.normalization_loaded = True
            self.status.fusion_loaded = True
        except ApplicationError as exc:
            self._record_error(exc.code)
            if self.settings.REQUIRE_ALL_MODELS:
                raise

    @staticmethod
    def _read_checked_config(
        path: Path,
        schema: type[ScoreNormalizationConfig] | type[FusionConfig],
    ) -> ScoreNormalizationConfig | FusionConfig:
        if not path.is_file():
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "Falta una configuración de integración calibrada.",
                503,
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("config root")
            checksum = payload.get("checksum")
            if checksum != canonical_checksum(payload):
                raise ValueError("config checksum")
            return schema.model_validate(payload)
        except (
            OSError,
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "Una configuración de integración no es válida.",
                503,
            ) from exc

    def _load_facial(self) -> None:
        record = self._single_family_record("facial")
        if record is None:
            self.status.facial.reason_code = "FACIAL_MODEL_UNAVAILABLE"
            self._record_error("FACIAL_MODEL_UNAVAILABLE")
            return
        try:
            threshold = self._threshold(record, "selected_threshold")
            if not record.record.model_name:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "El registro facial no declara model_name.",
                    503,
                )
            self.facial_runtime = FacialRuntime(
                model_name=record.record.model_name,
                model_version=record.record.model_version,
                model_root=self.paths.insightface_model_root,
                templates_path=None,
                threshold=threshold,
                device=self.status.device,
                template_paths=tuple(
                    artifact.path
                    for artifact in record.artifacts
                    if artifact.path.suffix.casefold() == ".npz"
                ),
            )
            self.status.facial.available = True
            self.status.facial.loaded = True
            self.status.facial.checksum_valid = True
            self.status.facial.version = record.record.model_version
        except ApplicationError as exc:
            self.status.facial.reason_code = exc.code
            self._record_error(exc.code)
            if self.settings.REQUIRE_ALL_MODELS:
                raise

    def _load_pad(self) -> None:
        record = self._single_family_record("pad")
        if record is None:
            self.status.pad.reason_code = "PAD_MODEL_UNAVAILABLE"
            self._record_error("PAD_MODEL_UNAVAILABLE")
            return
        try:
            exported_models = [
                artifact.path
                for artifact in record.artifacts
                if artifact.path.suffix.casefold() == ".keras"
                and "exported" in {
                    part.casefold() for part in artifact.path.parts
                }
            ]
            if len(exported_models) != 1:
                raise ApplicationError(
                    "MODEL_ARTIFACT_INVALID",
                    "El bundle PAD no contiene un único modelo exportado.",
                    503,
                )
            model_path = exported_models[0]
            model = PadRuntime.load_model(model_path)
            threshold = self._threshold(record, "selected_threshold")
            self.pad_runtime = PadRuntime(
                model=model,
                model_version=record.record.model_version,
                threshold=threshold,
            )
            self.status.pad.available = True
            self.status.pad.loaded = True
            self.status.pad.checksum_valid = True
            self.status.pad.version = record.record.model_version
        except ApplicationError as exc:
            self.status.pad.reason_code = exc.code
            self._record_error(exc.code)
            if self.settings.REQUIRE_ALL_MODELS:
                raise

    def _single_family_record(
        self, family: str
    ) -> ValidatedModelRecord | None:
        if self.snapshot is None:
            return None
        records = self.snapshot.family(family)
        if not records:
            return None
        if len(records) != 1:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El registro selecciona más de un modelo para una familia.",
                503,
            )
        return records[0]

    @staticmethod
    def _threshold(
        record: ValidatedModelRecord, field: str
    ) -> float:
        candidates = [
            artifact.path
            for artifact in record.artifacts
            if artifact.path.suffix.casefold() == ".json"
            and (
                "threshold" in artifact.path.name.casefold()
                or artifact.role == "threshold"
                or "thresholds"
                in {part.casefold() for part in artifact.path.parts}
            )
        ]
        if len(candidates) != 1:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El bundle no contiene un umbral inequívoco.",
                503,
            )
        try:
            payload = json.loads(candidates[0].read_text(encoding="utf-8"))
            threshold = float(payload[field])
        except (KeyError, OSError, TypeError, ValueError) as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El umbral registrado no es numérico.",
                503,
            ) from exc
        if (
            payload.get("model_version") != record.record.model_version
            or payload.get("dataset_version")
            != record.record.dataset_version
            or payload.get("test_rows_used") != 0
        ):
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El umbral no coincide con la versión registrada.",
                503,
            )
        if not 0 <= threshold <= 1:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El umbral registrado está fuera de rango.",
                503,
            )
        return threshold

    def get_behavioral_runtime(
        self, participant_code: str
    ) -> BehavioralRuntime:
        record = self._behavioral_records.get(participant_code)
        if record is None:
            raise ApplicationError(
                "BEHAVIORAL_MODEL_UNAVAILABLE",
                "El participante aún no tiene un modelo conductual.",
                409,
            )
        with self._cache_lock:
            cached = self._behavioral_cache.get(participant_code)
            if cached is not None:
                self._behavioral_cache.move_to_end(participant_code)
                return cached
            participant_lock = self._participant_locks.setdefault(
                participant_code, RLock()
            )
        with participant_lock:
            with self._cache_lock:
                cached = self._behavioral_cache.get(participant_code)
                if cached is not None:
                    self._behavioral_cache.move_to_end(participant_code)
                    return cached
            runtime = BehavioralRuntime.from_artifacts(
                self._behavioral_artifacts(record),
                model_version=record.record.model_version,
                dataset_version=record.record.dataset_version,
            )
            with self._cache_lock:
                self._behavioral_cache[participant_code] = runtime
                self._behavioral_cache.move_to_end(participant_code)
                if self.settings.BEHAVIORAL_MODEL_LOADING_MODE == "lru":
                    while (
                        len(self._behavioral_cache)
                        > self.settings.BEHAVIORAL_MODEL_CACHE_SIZE
                    ):
                        self._behavioral_cache.popitem(last=False)
                self.status.behavioral_loaded = len(
                    self._behavioral_cache
                )
            return runtime

    @staticmethod
    def _behavioral_artifacts(
        record: ValidatedModelRecord,
    ) -> BehavioralArtifactPaths:
        by_name = {
            artifact.path.name: artifact.path
            for artifact in record.artifacts
        }
        try:
            return BehavioralArtifactPaths(
                model=by_name["autoencoder.keras"],
                scaler=by_name["scaler.joblib"],
                threshold=by_name["threshold.json"],
                feature_schema=by_name["feature_schema.json"],
                metadata=by_name["metadata.json"],
            )
        except KeyError as exc:
            raise ApplicationError(
                "MODEL_ARTIFACT_INVALID",
                "El bundle conductual está incompleto.",
                503,
            ) from exc
