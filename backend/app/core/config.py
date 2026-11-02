import logging
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "DayFlow"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "insecure-secret-key-change-me"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/dayflow_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # JWT and Authentication Settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Refresh Cookie Settings
    REFRESH_COOKIE_NAME: str = "dayflow_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def validate_security(self) -> None:
        """Validate security-critical configuration on application startup."""
        if self.APP_ENV == "production":
            if self.SECRET_KEY in ("insecure-secret-key-change-me", "replace-this-with-a-secure-random-secret-key-in-production"):
                raise ValueError("Insecure SECRET_KEY configured in production environment!")
            if not self.REFRESH_COOKIE_SECURE:
                raise ValueError("REFRESH_COOKIE_SECURE must be True in production!")


settings = Settings()


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
