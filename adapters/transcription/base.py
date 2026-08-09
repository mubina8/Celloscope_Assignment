"""
Transcription provider interface.

Any adapter (mock, self-hosted Whisper, cloud API) implements this ABC.
services/transcription_service.py depends only on this interface, never
on a concrete adapter or a provider SDK -- that's what layer separation
buys us: swap providers via config without touching orchestration logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    detected_language: str  # "bn" | "en"
    duration_seconds: float
    provider: str
    speech_detected: bool


class TranscriptionAdapter(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str, language: str) -> TranscriptionResult:
        """
        language: "bn", "en", or "auto".
        Raises core.errors.ProviderError on adapter-level failure.
        Must NOT raise on silence/no-speech input -- return a result with
        speech_detected=False and an empty transcript instead. See
        core/errors.py docstring on NoSpeechDetectedError for why this
        is a result, not an exception, at the service layer boundary.
        """
        raise NotImplementedError
