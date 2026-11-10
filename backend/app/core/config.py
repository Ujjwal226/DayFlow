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

    # Email & Verification Settings
    EMAIL_PROVIDER: str = "development"  # "development" or "smtp"
    EMAIL_FROM: str = "noreply@dayflow.app"
    EMAIL_FROM_NAME: str = "DayFlow"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting Settings for Auth Email Endpoints
    AUTH_EMAIL_RATE_LIMIT_IP_MAX_REQUESTS: int = 3
    AUTH_EMAIL_RATE_LIMIT_IP_WINDOW_MINUTES: int = 15
    AUTH_EMAIL_COOLDOWN_PER_EMAIL_MINUTES: int = 2
    RATE_LIMIT_SALT: str = "dayflow-rate-limit-salt-change-me"

    # Trusted Proxies (IPs or CIDRs whose X-Forwarded-For headers are trusted)
    TRUSTED_PROXIES: Union[List[str], str] = []

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def assemble_trusted_proxies(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

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
            if self.EMAIL_PROVIDER == "development":
                raise ValueError("Development email provider cannot be used in production environment!")
            if not self.RATE_LIMIT_SALT or self.RATE_LIMIT_SALT in (
                "dayflow-rate-limit-salt-change-me",
                "replace-with-a-secure-salt-for-rate-limiting-in-production",
            ) or len(self.RATE_LIMIT_SALT.strip()) < 16:
                raise ValueError(
                    "Production requires a strong, non-default RATE_LIMIT_SALT (at least 16 characters)!"
                )


settings = Settings()


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
