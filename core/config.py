"""
Typed application settings, loaded from environment variables.

Design choice: pydantic-settings gives us validation + type coercion for free,
and a single source of truth for "what env vars does this service read".
No secrets are committed; `.env.example` documents the shape without values.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Which adapter implementation to wire up. "mock" requires no network/model.
    transcription_provider: str = "mock"  # "mock" | "whisper" | "<vendor>"
    extraction_provider: str = "mock"     # "mock" | "<ocr-vendor>"

    # Real-provider credentials (only required if provider != "mock")
    openai_api_key: str | None = None
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None
    ocr_api_key: str | None = None

    # Validation limits
    max_upload_mb: int = 25

    # Mock adapter fixture locations
    mock_transcription_fixtures_dir: str = "adapters/transcription/fixtures"
    mock_extraction_fixtures_dir: str = "adapters/extraction/fixtures"


@lru_cache
def get_settings() -> Settings:
    return Settings()
