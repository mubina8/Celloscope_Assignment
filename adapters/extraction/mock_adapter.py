"""
Mock extraction adapter.

Replays recorded OCR line output from disk. No network call, no model
load. Fixture format: adapters/extraction/fixtures/<filename_stem>.json
    { "lines": [{"text": "...", "confidence": 0.94}, ...] }

Files with no matching fixture return a single low-confidence line
containing garbage text, simulating "this isn't a lab report" input,
so the not-a-lab-report degrade path (requirement #8) is exercisable
against mocks without needing a real OCR provider.
"""
import json
from pathlib import Path

from adapters.extraction.base import ExtractionAdapter, OcrLine, OcrResult


class MockExtractionAdapter(ExtractionAdapter):
    def __init__(self, fixtures_dir: str):
        self._fixtures_dir = Path(fixtures_dir)

    def run_ocr(self, image_bytes: bytes, filename: str) -> OcrResult:
        stem = Path(filename).stem
        fixture_path = self._fixtures_dir / f"{stem}.json"

        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            lines = [OcrLine(text=l["text"], confidence=l.get("confidence")) for l in data["lines"]]
            return OcrResult(lines=lines, provider="mock")

        return OcrResult(
            lines=[OcrLine(text="illegible scanned content, no structure detected", confidence=0.12)],
            provider="mock",
        )
