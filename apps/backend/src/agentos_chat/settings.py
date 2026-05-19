from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnvironment = Literal["local", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentos_chat"
    mock_auth_subject: str = "mock|local-dev-user"
    cors_origins: str = "http://localhost:4321"
    openrouter_api_key: str = ""
    agno_telemetry: bool = False
    agent_model: str = "openrouter/google/gemini-2.0-flash-001"
    request_timeout_seconds: int = 60
    langwatch_api_key: str = ""
    langwatch_endpoint: str = ""
    app_environment: AppEnvironment = "local"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
