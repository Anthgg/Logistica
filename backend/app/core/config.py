from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Validated application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Continuous Authentication API"
    APP_VERSION: str = "0.9.8"
    APP_ENV: Literal["local", "development", "testing", "staging", "production"] = "local"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["text", "json"] = "text"
    STORAGE_PROVIDER: Literal["local", "gcs", "s3"] = "local"
    # Raiz del storage documental. Docker monta aqui un volumen con vida
    # propia; sin configurar se usa la ruta derivada del backend.
    DOCUMENT_STORAGE_PATH: str | None = None
    FRONTEND_URL: str = "http://localhost:5173"
    DEFAULT_LOCALE: Literal["es", "en", "pt"] = "es"
    SECRET_KEY: str = Field(default="development-only-change-me", min_length=16, repr=False)
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None
    SESSION_COOKIE_NAME: str = "session_token"
    REFRESH_COOKIE_NAME: str = "refresh_token"
    DEVICE_COOKIE_NAME: str = "device_token"
    CSRF_COOKIE_NAME: str = "csrf_token"
    SESSION_EXPIRE_MINUTES: int = Field(default=480, ge=5)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=5, le=60)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    REMEMBER_SESSION_EXPIRE_DAYS: int = Field(default=30, ge=1, le=90)
    SESSION_IDLE_TIMEOUT_MINUTES: int = Field(default=60, ge=1)
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    PASSWORD_MIN_LENGTH: int = Field(default=10, ge=10, le=128)
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, ge=1)
    ACCOUNT_LOCK_MINUTES: int = Field(default=15, ge=1)
    SESSION_ACTIVITY_UPDATE_SECONDS: int = Field(default=60, ge=10)
    RATE_LIMIT_REQUESTS: int = Field(default=10, ge=1)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)
    CAPTURE_STORAGE_MODE: Literal["local"] = "local"
    CAPTURE_LOCAL_PATH: str = "../data/captures"
    CAPTURE_MAX_FILE_SIZE: int = Field(default=1_048_576, ge=1024)
    FACIAL_CAPTURE_INTERVAL_SECONDS: int = Field(default=5, ge=1)
    BEHAVIOR_BATCH_INTERVAL_SECONDS: int = Field(default=3, ge=1)
    BEHAVIOR_BATCH_MAX_EVENTS: int = Field(default=100, ge=1, le=1000)
    BEHAVIOR_BATCH_MAX_PAYLOAD_BYTES: int = Field(default=262_144, ge=1024)
    EXPERIMENTAL_SESSION_STALE_MINUTES: int = Field(default=15, ge=5)
    RESEARCH_MAX_ACTIVE_SESSIONS_PER_USER: int = Field(default=1, ge=1, le=5)
    RESEARCH_MIN_SESSION_DURATION_SECONDS: int = Field(default=10, ge=0, le=3600)
    RESEARCH_PROTOCOL_VERSION: str = Field(default="pilot-protocol-v0.1.0", max_length=50)
    RESEARCH_COLLECTOR_VERSION: str = Field(default="web-v0.1.0", max_length=50)
    DATABASE_URL: str = Field(default="sqlite:////app/data/app.db")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=1800, ge=1)
    MODEL_PATH: str = "../models"
    MODEL_REGISTRY_PATH: str = "../models/registry/model_registry.json"
    FACIAL_MODEL_VERSION: str = "facial-arcface-v0.1.0"
    PAD_MODEL_VERSION: str = "pad-mobilenetv2-v0.1.0"
    BEHAVIORAL_MODEL_VERSION_PREFIX: str = "behavioral-ae"
    FACIAL_TEMPLATES_PATH: str = "../models/facial/templates"
    FACIAL_THRESHOLD_PATH: str = "../models/facial/thresholds"
    INSIGHTFACE_MODEL_ROOT: str = "../models/facial/insightface"
    PAD_MODEL_PATH: str = "../models/pad/exported"
    PAD_THRESHOLD_PATH: str = "../models/pad/thresholds"
    BEHAVIORAL_MODELS_PATH: str = "../models/behavioral/participants"
    BEHAVIORAL_FEATURES_PATH: str = (
        "../data/processed/behavioral/behavioral_features.parquet"
    )
    FUSION_CONFIG_PATH: str = "../models/fusion/fusion_config.json"
    NORMALIZATION_CONFIG_PATH: str = (
        "../models/fusion/score_normalization.json"
    )
    MODEL_DEVICE: Literal["auto", "cpu", "gpu"] = "auto"
    MODEL_LOAD_ON_STARTUP: bool = True
    MODEL_STRICT_CHECKSUM: bool = True
    CONTINUOUS_AUTH_ENABLED: bool = True
    CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS: int = Field(default=5, ge=1, le=300)
    CONTINUOUS_AUTH_MAX_BATCH_WINDOWS: int = Field(default=10, ge=1, le=100)
    RISK_LOW_MAX: float = Field(default=0.30, ge=0, le=1)
    RISK_MEDIUM_MAX: float = Field(default=0.60, ge=0, le=1)
    RISK_HIGH_MAX: float = Field(default=0.80, ge=0, le=1)
    REQUIRE_ALL_MODELS: bool = False
    INFERENCE_TIMEOUT_SECONDS: int = Field(default=10, ge=1, le=120)
    BEHAVIORAL_MODEL_LOADING_MODE: Literal["eager", "lazy", "lru"] = "lru"
    BEHAVIORAL_MODEL_CACHE_SIZE: int = Field(default=20, ge=1, le=500)
    MINIMUM_AVAILABLE_COMPONENTS: int = Field(default=2, ge=1, le=3)
    AUTO_REVOKE_CRITICAL_SESSION: bool = False
    RISK_HIGH_CONFIRMATION_COUNT: int = Field(default=2, ge=1, le=20)
    RISK_CRITICAL_CONFIRMATION_COUNT: int = Field(default=2, ge=1, le=20)
    RISK_RECOVERY_CONFIRMATION_COUNT: int = Field(default=3, ge=1, le=20)
    RISK_EVALUATION_WINDOW_SECONDS: int = Field(default=60, ge=5, le=3600)
    GEOCODING_PROVIDER: str = "nominatim"
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "LogisticaT1-BranchLocator/1.0 (contact@logisticat1.pe)"
    NOMINATIM_TIMEOUT_SECONDS: float = Field(default=5.0, ge=0.5, le=60.0)
    NOMINATIM_MIN_INTERVAL_SECONDS: float = Field(default=1.0, ge=0.1, le=10.0)
    GEOCODING_CACHE_TTL_SECONDS: int = Field(default=3600, ge=60)
    GEOCODING_CACHE_MAX_ENTRIES: int = Field(default=1000, ge=10, le=100000)

    @field_validator(
        "APP_NAME",
        "APP_VERSION",
        "FRONTEND_URL",
        "DATABASE_URL",
        "MODEL_PATH",
        "MODEL_REGISTRY_PATH",
        "FACIAL_MODEL_VERSION",
        "PAD_MODEL_VERSION",
        "BEHAVIORAL_MODEL_VERSION_PREFIX",
        "FACIAL_TEMPLATES_PATH",
        "FACIAL_THRESHOLD_PATH",
        "INSIGHTFACE_MODEL_ROOT",
        "PAD_MODEL_PATH",
        "PAD_THRESHOLD_PATH",
        "BEHAVIORAL_MODELS_PATH",
        "BEHAVIORAL_FEATURES_PATH",
        "FUSION_CONFIG_PATH",
        "NORMALIZATION_CONFIG_PATH",
        "RESEARCH_PROTOCOL_VERSION",
        "RESEARCH_COLLECTOR_VERSION",
        "NOMINATIM_BASE_URL",
        "NOMINATIM_USER_AGENT",
    )
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("API_PREFIX")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized = value.rstrip("/") or "/"
        if not normalized.startswith("/"):
            raise ValueError("API_PREFIX must start with '/'")
        return normalized

    @field_validator("DATABASE_URL")
    @classmethod
    def use_psycopg_three(cls, value: str) -> str:
        if value.startswith("sqlite://"):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL with Psycopg 3")
        return value

    @field_validator("COOKIE_DOMAIN", mode="before")
    @classmethod
    def empty_cookie_domain_is_none(cls, value: str | None) -> str | None:
        return value or None

    def model_post_init(self, context: object) -> None:
        if self.SESSION_COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("SameSite=None requires COOKIE_SECURE=true")
        if self.APP_ENV == "production" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SECURE must be true in production")

    @model_validator(mode="after")
    def validate_risk_boundaries(self) -> "Settings":
        if not (
            self.RISK_LOW_MAX
            < self.RISK_MEDIUM_MAX
            < self.RISK_HIGH_MAX
            < 1
        ):
            raise ValueError(
                "Risk boundaries must be strictly increasing and below 1."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
