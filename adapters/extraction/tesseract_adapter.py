"""
Real extraction adapter using Tesseract OCR (self-hosted, via pytesseract).

Chosen over a cloud OCR API to avoid a second paid credential in a
public repo; rejected self-hosting a heavier layout-aware model to keep
image off the default compose path (requirement #11). See DECISIONS.md.

Only module that imports pytesseract/PIL, per requirement #10.
"""
import io

import pytesseract
from PIL import Image

from adapters.extraction.base import ExtractionAdapter, OcrLine, OcrResult
from core.errors import ProviderError


class TesseractExtractionAdapter(ExtractionAdapter):
    def run_ocr(self, image_bytes: bytes, filename: str) -> OcrResult:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Group words into lines using Tesseract's line index, keep per-line
            # average confidence. This preserves raw line text for raw_line
            # (requirement #5) without us re-flowing/cleaning it.
            line_groups: dict[tuple[int, int, int], list[tuple[str, float]]] = {}
            for i, text in enumerate(data["text"]):
                if not text.strip():
                    continue
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                conf = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
                line_groups.setdefault(key, []).append((text, conf))

            lines = []
            for words in line_groups.values():
                text = " ".join(w for w, _ in words)
                avg_conf = sum(c for _, c in words) / len(words) / 100.0
                lines.append(OcrLine(text=text, confidence=avg_conf))

            return OcrResult(lines=lines, provider="tesseract")
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Tesseract OCR failed: {exc}") from exc
