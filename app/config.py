"""Configurações globais da aplicação Flux-Capacitor."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.6

    # LangFuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = False

    # App
    APP_NAME: str = "Flux-Capacitor"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # DB
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/flux_capacitor.db"
    DATABASE_SYNC_URL: str = "sqlite:///./data/flux_capacitor.db"

    # API
    API_KEY_HEADER: str = "X-API-Key"
    API_DEFAULT_KEY: str = "change-me-flux-capacitor-key"

    # CORS
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # Unsplash
    UNSPLASH_BASE: str = "https://source.unsplash.com"

    # Uploads
    UPLOAD_DIR: str = "./data/uploads"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
