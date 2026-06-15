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
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        validation_alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    )
    login_rate_limit_max_attempts: int = Field(
        default=5,
        validation_alias="LOGIN_RATE_LIMIT_MAX_ATTEMPTS",
    )
    login_rate_limit_window_seconds: int = Field(
        default=900,
        validation_alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS",
    )
    dev_super_admin_email: str = Field(
        default="admin@acme.example",
        validation_alias="DEV_SUPER_ADMIN_EMAIL",
    )
    dev_super_admin_password: str = Field(
        default="SecurePass123!",
        validation_alias="DEV_SUPER_ADMIN_PASSWORD",
    )
    credential_encryption_key: str = Field(
        default="change_me_32_byte_encryption_key_dev",
        validation_alias="CREDENTIAL_ENCRYPTION_KEY",
    )
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        validation_alias="CORS_ORIGINS",
    )

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(cls, data: object) -> object:
        if isinstance(data, dict):
            raw = data.get("CORS_ORIGINS") or data.get("cors_origins")
            if isinstance(raw, str) and raw.strip():
                data = {**data, "CORS_ORIGINS": [o.strip() for o in raw.split(",")]}
        return data

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment != "development":
            if self.jwt_secret_key.startswith("change_me"):
                msg = (
                    "JWT_SECRET_KEY must be set to a non-placeholder value "
                    "in non-development environments"
                )
                raise ValueError(msg)
            if self.credential_encryption_key.startswith("change_me"):
                msg = (
                    "CREDENTIAL_ENCRYPTION_KEY must be set to a non-placeholder "
                    "value in non-development environments"
                )
                raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
