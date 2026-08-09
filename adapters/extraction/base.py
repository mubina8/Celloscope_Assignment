"""
Document/OCR provider interface.

Adapters return raw OCR text/lines only -- NOT structured meta/results.
Structuring (splitting header vs table, mapping to fields) is business
logic and lives in services/, per requirement #10 (no provider SDK
outside adapters/, and orchestration stays out of adapters/).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class OcrResult:
    lines: list[OcrLine]
    provider: str


class ExtractionAdapter(ABC):
    @abstractmethod
    def run_ocr(self, image_bytes: bytes, filename: str) -> OcrResult:
        """Raises core.errors.ProviderError on adapter-level failure."""
        raise NotImplementedError
