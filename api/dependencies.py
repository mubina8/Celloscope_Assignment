"""
FastAPI dependency providers. This is the single place that decides
which adapter implementation to construct, based on Settings -- the
"decided by configuration, not a code change" requirement (#1/#4).
"""
from functools import lru_cache

from adapters.extraction.base import ExtractionAdapter
from adapters.extraction.mock_adapter import MockExtractionAdapter
from adapters.transcription.base import TranscriptionAdapter
from adapters.transcription.mock_adapter import MockTranscriptionAdapter
from core.config import Settings, get_settings
from services.extraction_service import ExtractionService
from services.transcription_service import TranscriptionService


@lru_cache
def get_transcription_adapter() -> TranscriptionAdapter:
    settings: Settings = get_settings()
    if settings.transcription_provider == "mock":
        return MockTranscriptionAdapter(settings.mock_transcription_fixtures_dir)
    if settings.transcription_provider == "whisper":
        from adapters.transcription.whisper_adapter import WhisperTranscriptionAdapter  # local import: keep SDK optional
        if not settings.openai_api_key:
            raise RuntimeError("TRANSCRIPTION_PROVIDER=whisper requires OPENAI_API_KEY")
        return WhisperTranscriptionAdapter(settings.openai_api_key)
    raise RuntimeError(f"Unknown transcription provider: {settings.transcription_provider}")


@lru_cache
def get_extraction_adapter() -> ExtractionAdapter:
    settings: Settings = get_settings()
    if settings.extraction_provider == "mock":
        return MockExtractionAdapter(settings.mock_extraction_fixtures_dir)
    if settings.extraction_provider == "tesseract":
        from adapters.extraction.tesseract_adapter import TesseractExtractionAdapter  # local import: keep dep optional
        return TesseractExtractionAdapter()
    raise RuntimeError(f"Unknown extraction provider: {settings.extraction_provider}")


def get_transcription_service() -> TranscriptionService:
    return TranscriptionService(get_transcription_adapter())


def get_extraction_service() -> ExtractionService:
    return ExtractionService(get_extraction_adapter())
