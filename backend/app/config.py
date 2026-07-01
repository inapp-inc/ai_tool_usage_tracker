"""Environment configuration (NFR-SEC-008)."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, PostgresDsn, model_validator
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
    environment: EnvironmentName = Field(
        default="development",
        validation_alias="ENVIRONMENT",
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
    super_admin_email: str = Field(
        default="admin@example.com",
        validation_alias=AliasChoices("SUPER_ADMIN_EMAIL", "DEV_SUPER_ADMIN_EMAIL"),
    )
    super_admin_password: str = Field(
        default="123456789",
        validation_alias=AliasChoices("SUPER_ADMIN_PASSWORD", "DEV_SUPER_ADMIN_PASSWORD"),
    )
    seed_super_admin_on_startup: bool = Field(
        default=False,
        validation_alias="SEED_SUPER_ADMIN_ON_STARTUP",
    )
    sync_super_admin_credentials: bool = Field(
        default=True,
        validation_alias="SEED_SUPER_ADMIN_SYNC_CREDENTIALS",
    )
    collector_encryption_key: str = Field(
        default="change_me_collector_encryption_key_dev",
        validation_alias="COLLECTOR_ENCRYPTION_KEY",
    )
    collector_scheduler_enabled: bool = Field(
        default=True,
        validation_alias="COLLECTOR_SCHEDULER_ENABLED",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    frontend_port: int = Field(
        default=5173,
        validation_alias="FRONTEND_PORT",
    )
    cors_origins: str = Field(
        default="",
        validation_alias="CORS_ORIGINS",
    )
    local_storage_root: str = Field(
        default="./data/storage",
        validation_alias="LOCAL_STORAGE_ROOT",
    )
    cursor_pull_dump_enabled: bool = Field(
        default=False,
        validation_alias="CURSOR_PULL_DUMP_ENABLED",
    )
    copilot_pull_dump_enabled: bool = Field(
        default=False,
        validation_alias="COPILOT_PULL_DUMP_ENABLED",
    )
    openai_pull_dump_enabled: bool = Field(
        default=False,
        validation_alias="OPENAI_PULL_DUMP_ENABLED",
    )

    def resolved_cors_origins(self) -> list[str]:
        """Explicit browser origins from CORS_ORIGINS (always merged when set)."""
        if not self.cors_origins.strip():
            return []
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def cors_origin_regex(self) -> str | None:
        """Permissive dev regex when CORS_ORIGINS is not set (localhost, LAN, hostnames)."""
        if self.cors_origins.strip() or self.environment != "development":
            return None
        return r"https?://[\w.-]+(:\d+)?"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment != "development":
            if self.jwt_secret_key.startswith("change_me"):
                msg = "JWT_SECRET_KEY must be set in non-development environments"
                raise ValueError(msg)
            if self.collector_encryption_key.startswith("change_me"):
                msg = "COLLECTOR_ENCRYPTION_KEY must be set in non-development environments"
                raise ValueError(msg)
            if not self.cors_origins.strip():
                msg = "CORS_ORIGINS must be set in non-development environments"
                raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
