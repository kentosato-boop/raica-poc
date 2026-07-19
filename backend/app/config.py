from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
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
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://127.0.0.1:8001"
    bootstrap_schema_enabled: bool = True
    demo_seed_enabled: bool = True
    startup_matching_enabled: bool = True
    skill_sheet_storage_dir: str = str(ROOT / "data" / "skill_sheets")

    porters_candidates_url: str | None = None
    porters_jobs_url: str | None = None
    porters_token: str | None = None
    gmail_webhook_url: str | None = None
    gmail_access_token: str | None = None
    gmail_sender: str | None = None
    zalo_webhook_url: str | None = None
    asana_webhook_url: str | None = None
    integration_timeout_seconds: float = 15.0

    # AI分析（推薦上位の適合理由をLLMで生成）。キー未設定ならルールベース説明へフォールバックする。
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RAICA_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    )
    llm_model: str = "claude-sonnet-5"
    llm_analysis_enabled: bool = True
    llm_timeout_seconds: float = 30.0

    @property
    def llm_configured(self) -> bool:
        return bool(self.anthropic_api_key) and self.llm_analysis_enabled

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def provider_url(self, provider: str) -> str | None:
        return {
            "gmail": self.gmail_webhook_url,
            "zalo": self.zalo_webhook_url,
            "asana": self.asana_webhook_url,
        }.get(provider)

    @property
    def gmail_configured(self) -> bool:
        return bool(self.gmail_access_token and self.gmail_sender) or bool(self.gmail_webhook_url)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_runtime_settings(settings: Settings) -> None:
    if settings.is_production and not settings.api_key:
        raise RuntimeError("RAICA_API_KEY is required in production")
