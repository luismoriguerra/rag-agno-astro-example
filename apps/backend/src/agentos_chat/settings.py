from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnvironment = Literal["local", "staging", "production", "test"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentos_chat"
    auth0_domain: str = ""
    auth0_issuer: str = ""
    auth0_api_audience: str = ""
    auth0_jwt_test_mode: bool = False
    auth0_jwt_test_secret: str = "test-jwt-secret-at-least-32-characters-long"
    cors_origins: str = "http://localhost:4321"
    openrouter_api_key: str = ""
    agno_telemetry: bool = False
    agent_model: str = "openrouter/google/gemini-2.0-flash-001"
    request_timeout_seconds: int = 60
    langwatch_api_key: str = ""
    langwatch_endpoint: str = ""
    app_environment: AppEnvironment = "local"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_skip_signature_validation: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def auth0_jwks_url(self) -> str:
        return f"{self.auth0_issuer.rstrip('/')}/.well-known/jwks.json"

    @property
    def auth0_configured(self) -> bool:
        return bool(self.auth0_domain and self.auth0_issuer and self.auth0_api_audience)

    @property
    def whatsapp_configured(self) -> bool:
        return bool(
            self.whatsapp_access_token
            and self.whatsapp_phone_number_id
            and self.whatsapp_verify_token
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
