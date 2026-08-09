"""
Transcription orchestration. No FastAPI types here (requirement #10) --
input is plain bytes/str, output is a plain dataclass/dict the api/ layer
serialises into a response model.
"""
from dataclasses import dataclass

from adapters.transcription.base import TranscriptionAdapter

SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class TranscribeResponse:
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str
    speech_detected: bool


class TranscriptionService:
    def __init__(self, adapter: TranscriptionAdapter):
        self._adapter = adapter

    def transcribe(self, audio_bytes: bytes, filename: str, language: str) -> TranscribeResponse:
        result = self._adapter.transcribe(audio_bytes, filename, language)
        return TranscribeResponse(
            transcript=result.transcript,
            detected_language=result.detected_language,
            duration_seconds=result.duration_seconds,
            provider=result.provider,
            speech_detected=result.speech_detected,
        )
