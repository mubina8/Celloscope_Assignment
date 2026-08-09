"""
Real transcription adapter, calling OpenAI's Whisper API.

Chosen because it handles Bengali + English + auto-detect out of the box
with one call, no self-hosted model to keep off the default compose path
(requirement #11). See DECISIONS.md for what we rejected instead.

This module is the ONLY place the `openai` SDK is imported, per
requirement #10 -- services/ and api/ never see it.
"""
import io
import time

from openai import OpenAI

from adapters.transcription.base import TranscriptionAdapter, TranscriptionResult
from core.errors import ProviderError

# Heuristic: Whisper doesn't return a silence flag directly. We treat a
# transcript that is empty or whitespace-only after stripping as no-speech.
# Documented limitation -- see README known limitations.


class WhisperTranscriptionAdapter(TranscriptionAdapter):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    def transcribe(self, audio_bytes: bytes, filename: str, language: str) -> TranscriptionResult:
        try:
            start = time.monotonic()
            file_obj = io.BytesIO(audio_bytes)
            file_obj.name = filename

            kwargs = {}
            if language in ("bn", "en"):
                kwargs["language"] = language
            # language == "auto" -> omit, let Whisper detect

            response = self._client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
                response_format="verbose_json",
                **kwargs,
            )
            elapsed = time.monotonic() - start

            transcript = (response.text or "").strip()
            detected_language = getattr(response, "language", language if language != "auto" else "en")

            return TranscriptionResult(
                transcript=transcript,
                detected_language=detected_language,
                duration_seconds=getattr(response, "duration", elapsed),
                provider="whisper",
                speech_detected=bool(transcript),
            )
        except Exception as exc:  # noqa: BLE001 -- deliberately broad, translated to ProviderError
            raise ProviderError(f"Whisper transcription failed: {exc}") from exc
