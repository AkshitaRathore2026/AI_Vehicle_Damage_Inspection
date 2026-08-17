from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AI Vehicle Damage Inspection System"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    database_url: str = Field(
        default="postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/vehicle_damage_inspection"
    )

    jwt_secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    redis_url: str = "redis://localhost:6379/0"

    model_path: str = "ml/weights/best.pt"
    model_name: str = "vehicle-damage-yolo"
    model_version: str = "0.1.0-poc"
    model_confidence_threshold: float = 0.35
    use_mock_detector: bool = True

    upload_dir: str = "storage/uploads"
    processed_dir: str = "storage/processed"
    report_dir: str = "storage/reports"

    max_upload_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png"
    backend_cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @field_validator("database_url")
    @classmethod
    def ensure_psycopg_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_image_type_list(self) -> list[str]:
        return [
            image_type.strip()
            for image_type in self.allowed_image_types.split(",")
            if image_type.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
