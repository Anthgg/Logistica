from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.paths import TRAINING_ROOT, DataPaths, resolve_from_training


class SplitRatios(BaseModel):
    train: float = Field(gt=0, lt=1)
    validation: float = Field(gt=0, lt=1)
    test: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def validate_total(self) -> "SplitRatios":
        if abs(self.train + self.validation + self.test - 1.0) > 1e-9:
            raise ValueError("Los porcentajes de partición deben sumar 1.")
        return self


class PipelineConfig(BaseModel):
    dataset_version: str
    data_root: str
    database_env_files: list[str]
    capture_storage_root: str
    capture_bucket: str | None = None
    facial_identity_manifest: str
    facial_pad_manifest: str
    behavioral_manifest: str
    dataset_splits: str
    frozen_test_manifest: str
    reports_root: str
    split_ratios: SplitRatios
    critical_leakage_checks: list[str]
    write_csv_copies: bool = True

    @property
    def paths(self) -> DataPaths:
        return DataPaths(resolve_from_training(self.data_root))


class ProtocolConfig(BaseModel):
    protocol_version: str
    pilot_participants: int = Field(ge=1)
    minimum_sessions_per_participant: int = Field(ge=1)
    scenarios: list[str]
    expected_session_duration: dict[str, tuple[int, int]]
    facial_capture_interval_seconds: int = Field(ge=1)
    behavioral_batch_interval_seconds: int = Field(ge=1)
    allowed_pad_attack_types: list[str]
    minimum_face_captures: int = Field(ge=0)
    minimum_behavioral_events: int = Field(ge=0)
    minimum_session_duration_seconds: int = Field(ge=0)
    maximum_session_error_rate: float = Field(ge=0, le=1)
    consent_version: str
    random_seed: int
    session_annotations: dict[str, dict[str, object]]


class FaceDetectorConfig(BaseModel):
    type: Literal["opencv_haar"] = "opencv_haar"
    scale_factor: float = Field(gt=1)
    min_neighbors: int = Field(ge=1)
    minimum_size: tuple[int, int]


class FaceQualityConfig(BaseModel):
    allowed_formats: list[str]
    maximum_file_size_bytes: int
    minimum_width: int
    minimum_height: int
    maximum_width: int
    maximum_height: int
    minimum_brightness_mean: float
    maximum_brightness_mean: float
    minimum_contrast: float
    minimum_laplacian_variance: float
    minimum_face_area_ratio: float
    face_border_margin_ratio: float
    minimum_capture_interval_seconds: float
    maximum_rejection_rate: float = Field(ge=0, le=1)
    reject_hidden_tab: bool
    face_detector: FaceDetectorConfig


class BehavioralConfig(BaseModel):
    window_size_seconds: int = Field(gt=0)
    stride_seconds: int = Field(gt=0)
    minimum_keyboard_events: int = Field(ge=0)
    minimum_mouse_events: int = Field(ge=0)
    maximum_idle_ratio: float = Field(ge=0, le=1)
    maximum_batch_events: int = Field(gt=0)
    maximum_timestamp_skew_seconds: int = Field(ge=0)
    maximum_dwell_time_ms: float
    minimum_flight_time_ms: float
    maximum_flight_time_ms: float
    maximum_interval_ms: float
    burst_pause_threshold_ms: float
    mouse_idle_threshold_ms: float
    maximum_missing_feature_ratio: float = Field(ge=0, le=1)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
    )
    DATABASE_URL: str

    @model_validator(mode="after")
    def validate_postgresql(self) -> "DatabaseSettings":
        if not self.DATABASE_URL.startswith(
            ("postgresql://", "postgresql+psycopg://")
        ):
            raise ValueError("DATABASE_URL debe usar PostgreSQL.")
        return self

    @property
    def sqlalchemy_url(self) -> str:
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self.DATABASE_URL


class PreparationConfig(BaseModel):
    pipeline: PipelineConfig
    protocol: ProtocolConfig
    face_quality: FaceQualityConfig
    behavioral: BehavioralConfig
    source_path: Path

    def database_settings(self) -> DatabaseSettings:
        env_files = [
            resolve_from_training(item)
            for item in self.pipeline.database_env_files
            if resolve_from_training(item).exists()
        ]
        return DatabaseSettings(_env_file=env_files or None)


class ImageSizeConfig(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ArcFaceTrainingConfig(BaseModel):
    model_name: str
    providers: list[str]
    embedding_dimension: int = Field(gt=0)
    detection_size: ImageSizeConfig
    minimum_detection_score: float = Field(ge=0, le=1)
    template_strategy: Literal["normalized_mean"]
    similarity_metric: Literal["cosine"]
    minimum_enrollment_images: int = Field(gt=0)
    maximum_enrollment_images: int = Field(gt=0)
    maximum_impostor_pairs_per_identity: int = Field(gt=0)
    threshold_objective: Literal["eer", "target_far"]
    target_far: float = Field(ge=0, le=1)
    random_seed: int
    dataset_version: str
    model_version: str

    @model_validator(mode="after")
    def validate_enrollment_range(self) -> "ArcFaceTrainingConfig":
        if self.maximum_enrollment_images < self.minimum_enrollment_images:
            raise ValueError("maximum_enrollment_images debe ser mayor o igual al mínimo.")
        return self


class AugmentationConfig(BaseModel):
    rotation: float = Field(ge=0)
    translation: float = Field(ge=0)
    zoom: float = Field(ge=0)
    contrast: float = Field(ge=0)
    brightness: float = Field(ge=0)


class PadTrainingConfig(BaseModel):
    image_size: ImageSizeConfig
    channels: int = Field(gt=0)
    backbone: Literal["MobileNetV2"]
    imagenet_weights: bool
    include_top: bool
    batch_size: int = Field(gt=0)
    epochs_frozen: int = Field(gt=0)
    epochs_finetuning: int = Field(gt=0)
    learning_rate_frozen: float = Field(gt=0)
    learning_rate_finetuning: float = Field(gt=0)
    dropout: float = Field(ge=0, lt=1)
    dense_units: int = Field(ge=0)
    fine_tune_last_layers: int = Field(gt=0)
    early_stopping_patience: int = Field(gt=0)
    reduce_lr_patience: int = Field(gt=0)
    label_smoothing: float = Field(ge=0, lt=1)
    class_weighting: bool
    cache_dataset: bool
    threshold_objective: Literal["minimum_acer", "target_apcer"]
    target_apcer: float = Field(ge=0, le=1)
    random_seed: int
    dataset_version: str
    model_version: str
    augmentation: AugmentationConfig


class AutoencoderArchitectureConfig(BaseModel):
    hidden_layers: list[int]
    latent_dimension: int = Field(gt=0)
    activation: str
    output_activation: str
    dropout: float = Field(ge=0, lt=1)
    l2_regularization: float = Field(ge=0)


class BehavioralTrainingConfig(BaseModel):
    feature_columns: list[str]
    minimum_train_windows_per_user: int = Field(gt=0)
    minimum_validation_windows_per_user: int = Field(gt=0)
    minimum_validation_impostor_windows: int = Field(gt=0)
    architecture: AutoencoderArchitectureConfig
    batch_size: int = Field(gt=0)
    epochs: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    early_stopping_patience: int = Field(gt=0)
    reduce_lr_patience: int = Field(gt=0)
    validation_fraction_from_train: float = Field(gt=0, lt=0.5)
    reconstruction_loss: Literal["mse"]
    threshold_method: Literal["percentile", "eer", "target_far", "maximum_f1"]
    threshold_percentile: float = Field(gt=0, lt=100)
    target_far: float = Field(ge=0, le=1)
    missing_value_strategy: Literal["reject"]
    random_seed: int
    dataset_version: str
    model_version_prefix: str

    @model_validator(mode="after")
    def validate_features(self) -> "BehavioralTrainingConfig":
        if not self.feature_columns or len(self.feature_columns) != len(
            set(self.feature_columns)
        ):
            raise ValueError("feature_columns debe ser una lista explícita sin duplicados.")
        return self


class ExperimentConfig(BaseModel):
    protocol_version: str
    dataset_version: str
    random_seed: int
    allowed_quality_statuses: list[str]
    training_splits: list[Literal["train", "validation"]]
    forbidden_split: Literal["test"]
    models_root: str
    reports_root: str
    registry_path: str
    experiments_path: str
    frozen_test_manifest: str
    frozen_test_checksum: str
    frozen_test_metadata: str
    deterministic_operations: bool


class TrainingConfigBundle(BaseModel):
    arcface: ArcFaceTrainingConfig
    pad: PadTrainingConfig
    behavioral: BehavioralTrainingConfig
    experiment: ExperimentConfig
    source_path: Path

    @model_validator(mode="after")
    def validate_versions(self) -> "TrainingConfigBundle":
        versions = {
            self.arcface.dataset_version,
            self.pad.dataset_version,
            self.behavioral.dataset_version,
            self.experiment.dataset_version,
        }
        if len(versions) != 1:
            raise ValueError("Todas las configuraciones deben usar el mismo dataset_version.")
        return self


def _read_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as source:
        content = yaml.safe_load(source) or {}
    if not isinstance(content, dict):
        raise ValueError(f"La configuración {path.name} debe ser un objeto YAML.")
    return content


def load_config(config_path: str | Path | None = None) -> PreparationConfig:
    config_dir = (
        resolve_from_training(config_path)
        if config_path
        else TRAINING_ROOT / "configs"
    )
    if config_dir.is_file():
        config_dir = config_dir.parent
    return PreparationConfig(
        pipeline=PipelineConfig.model_validate(
            _read_yaml(config_dir / "data_pipeline.yaml")
        ),
        protocol=ProtocolConfig.model_validate(
            _read_yaml(config_dir / "pilot_protocol.yaml")
        ),
        face_quality=FaceQualityConfig.model_validate(
            _read_yaml(config_dir / "face_quality.yaml")
        ),
        behavioral=BehavioralConfig.model_validate(
            _read_yaml(config_dir / "behavioral_features.yaml")
        ),
        source_path=config_dir,
    )


def load_training_configs(
    config_path: str | Path | None = None,
) -> TrainingConfigBundle:
    config_dir = (
        resolve_from_training(config_path)
        if config_path
        else TRAINING_ROOT / "configs"
    )
    if config_dir.is_file():
        config_dir = config_dir.parent
    return TrainingConfigBundle(
        arcface=ArcFaceTrainingConfig.model_validate(
            _read_yaml(config_dir / "arcface.yaml")
        ),
        pad=PadTrainingConfig.model_validate(
            _read_yaml(config_dir / "pad_mobilenetv2.yaml")
        ),
        behavioral=BehavioralTrainingConfig.model_validate(
            _read_yaml(config_dir / "behavioral_autoencoder.yaml")
        ),
        experiment=ExperimentConfig.model_validate(
            _read_yaml(config_dir / "experiment.yaml")
        ),
        source_path=config_dir,
    )
