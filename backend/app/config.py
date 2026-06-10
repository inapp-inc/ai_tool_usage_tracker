"""Environment configuration (NFR-SEC-008)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: PostgresDsn = Field(
        ...,
        validation_alias="DATABASE_URL",
    )
    redis_url: RedisDsn = Field(
        ...,
        validation_alias="REDIS_URL",
    )
    celery_broker_url: RedisDsn = Field(
        ...,
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: RedisDsn = Field(
        ...,
        validation_alias="CELERY_RESULT_BACKEND",
    )
    environment: EnvironmentName = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )
    storage_backend: str = Field(
        default="local",
        validation_alias="STORAGE_BACKEND",
    )
    local_storage_root: str = Field(
        default="/var/lib/ai-tracker/storage",
        validation_alias="LOCAL_STORAGE_ROOT",
    )
    jwt_secret_key: str = Field(
        default="change_me_jwt_secret_dev_only",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment != "development" and self.jwt_secret_key.startswith(
            "change_me"
        ):
            msg = "JWT_SECRET_KEY must be set to a non-placeholder value in non-development environments"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
