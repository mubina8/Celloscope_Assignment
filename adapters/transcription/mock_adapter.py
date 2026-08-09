"""
Mock transcription adapter.

Replays recorded responses from disk keyed by filename. No network call,
no model load -- this is what lets `docker compose up` work on a clean
clone with zero credentials (requirement #11).

Fixture format: adapters/transcription/fixtures/<filename_stem>.json
    {
      "transcript": "...",
      "detected_language": "bn",
      "duration_seconds": 4.2,
      "speech_detected": true
    }

Files with no matching fixture fall back to a generic canned response
rather than erroring, so ad-hoc smoke testing doesn't require a fixture
for every filename. Files named with a "silence" prefix are treated as
no-speech by convention if no fixture exists.
"""
import json
from pathlib import Path

from adapters.transcription.base import TranscriptionAdapter, TranscriptionResult


class MockTranscriptionAdapter(TranscriptionAdapter):
    def __init__(self, fixtures_dir: str):
        self._fixtures_dir = Path(fixtures_dir)

    def transcribe(self, audio_bytes: bytes, filename: str, language: str) -> TranscriptionResult:
        stem = Path(filename).stem
        fixture_path = self._fixtures_dir / f"{stem}.json"

        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            return TranscriptionResult(
                transcript=data["transcript"],
                detected_language=data.get("detected_language", "en" if language == "auto" else language),
                duration_seconds=data.get("duration_seconds", 0.0),
                provider="mock",
                speech_detected=data.get("speech_detected", True),
            )

        if "silence" in stem.lower() or "noise" in stem.lower():
            return TranscriptionResult(
                transcript="",
                detected_language="en" if language == "auto" else language,
                duration_seconds=2.0,
                provider="mock",
                speech_detected=False,
            )

        return TranscriptionResult(
            transcript="This is a mock transcript for testing purposes.",
            detected_language="en" if language == "auto" else language,
            duration_seconds=3.5,
            provider="mock",
            speech_detected=True,
        )
