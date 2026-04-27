from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "slm-hosting-balu-challenge1-weaction"
    environment: str = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    api_keys: list[str] = Field(default_factory=list)
    requests_per_minute: int = Field(default=60, ge=1)

    vllm_base_url: str = "http://vllm-qwen:8000/v1"
    vllm_api_key: str = "EMPTY"
    vllm_model: str = "qwen3.5-0.8b"
    primary_timeout_seconds: float = Field(default=30.0, ge=1.0)

    enable_fallback: bool = True
    fallback_base_url: str = "http://ollama:11434/v1"
    fallback_api_key: str = "ollama"
    fallback_model: str = "qwen3.5:0.8b"
    fallback_timeout_seconds: float = Field(default=60.0, ge=1.0)

    @field_validator("api_keys", mode="before")
    @classmethod
    def split_api_keys(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("vllm_base_url", "fallback_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
