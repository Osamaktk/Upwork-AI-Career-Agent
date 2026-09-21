from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Upwork AI Career Agent"
    app_env: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./career_agent.db"
    jwt_secret: str = "development-only-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    ai_primary_model: str = "gpt-5.6-sol"
    ai_fast_model: str = "gpt-5.6-luna"
    ai_provider_mode: Literal["disabled", "openai"] = "disabled"
    sample_jobs_dir: Path = Path("sample_jobs")
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("jwt_secret")
    @classmethod
    def validate_production_secret(cls, value: str, info):
        environment = info.data.get("app_env")
        if environment == "production" and len(value) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
