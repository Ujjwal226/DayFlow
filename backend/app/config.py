"""
DayFlow backend – application configuration.

Settings are read from environment variables (or a .env file via
python-dotenv).  No secrets are hard-coded here.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "sqlite:///./data/dayflow.db"

    @property
    def sync_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    # Accept a comma-separated string so the value can live in .env
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------ #
    # Authentication & Security
    # ------------------------------------------------------------------ #
    secret_key: str = "dayflow-stage5-insecure-development-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # ------------------------------------------------------------------ #
    # App environment
    # ------------------------------------------------------------------ #
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
