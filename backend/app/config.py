from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_prefix="RAICA_",
        extra="ignore",
    )

    app_name: str = "RAiCA API"
    environment: str = "development"
    database_url: str = f"sqlite:///{ROOT / 'data' / 'raica.sqlite3'}"
    api_key: str | None = None
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000"

    porters_candidates_url: str | None = None
    porters_jobs_url: str | None = None
    porters_token: str | None = None
    gmail_webhook_url: str | None = None
    zalo_webhook_url: str | None = None
    asana_webhook_url: str | None = None
    integration_timeout_seconds: float = 15.0

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def provider_url(self, provider: str) -> str | None:
        return {
            "gmail": self.gmail_webhook_url,
            "zalo": self.zalo_webhook_url,
            "asana": self.asana_webhook_url,
        }.get(provider)


@lru_cache
def get_settings() -> Settings:
    return Settings()
