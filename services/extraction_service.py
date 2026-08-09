"""
Lab report extraction orchestration.

Takes raw OCR lines from an adapter and structures them into the
meta/results shape. This is business logic (not OCR, not HTTP), so it
lives here per the layer rules -- adapters/ only ever returns raw lines.
"""
import re
from dataclasses import dataclass, field

from adapters.extraction.base import ExtractionAdapter
from services.normalization import normalize_date, normalize_unit, normalize_value

# A row is treated as a result row if it contains a recognisable value
# token (number, <X, >X, range, or scientific notation) AND at least
# one more whitespace-separated token before it (the test name).
_VALUE_TOKEN_RE = re.compile(
    r"(<\s*[\d.]+|>\s*[\d.]+|[\d.]+\s*[-–]\s*[\d.]+|[\d.]+\s*[xX×]\s*10\s*\^?\s*-?\d+|\d[\d,]*\.?\d*)"
)

_META_PATTERNS = {
    "patient_name": re.compile(r"(?:patient\s*name|name)\s*[:\-]\s*(.+)", re.IGNORECASE),
    "age": re.compile(r"age\s*[:\-]\s*([\d]+\s*(?:yrs?|years?)?)", re.IGNORECASE),
    "sex": re.compile(r"(?:sex|gender)\s*[:\-]\s*(male|female|m|f)\b", re.IGNORECASE),
    "report_date": re.compile(r"(?:report\s*date|date)\s*[:\-]\s*(.+)", re.IGNORECASE),
    "lab_name": re.compile(r"(?:lab(?:oratory)?\s*name|laboratory)\s*[:\-]\s*(.+)", re.IGNORECASE),
    "reference_no": re.compile(r"(?:ref(?:erence)?\s*(?:no|number|#)?)\s*[:\-]\s*(.+)", re.IGNORECASE),
}

# Minimum fraction of value-token-bearing lines required before we treat
# the document as a lab report at all (requirement #8: degrade gracefully
# on non-lab-report input rather than emitting fabricated structure).
_MIN_RESULT_LINES_FOR_LAB_REPORT = 1


@dataclass(frozen=True)
class ResultRow:
    test_name: str
    value: dict
    unit: str | None
    reference_range: str | None
    flag: str | None
    raw_line: str


@dataclass(frozen=True)
class ExtractResponse:
    meta: dict = field(default_factory=dict)
    results: list[ResultRow] = field(default_factory=list)
    is_lab_report: bool = True
    provider: str = "mock"


class ExtractionService:
    def __init__(self, adapter: ExtractionAdapter):
        self._adapter = adapter

    def extract(self, image_bytes: bytes, filename: str) -> ExtractResponse:
        ocr_result = self._adapter.run_ocr(image_bytes, filename)
        lines = [l.text for l in ocr_result.lines if l.text.strip()]

        meta = self._extract_meta(lines)
        results = self._extract_results(lines)

        # Graceful degradation: if we found neither meta fields nor
        # result rows, this probably isn't a lab report at all. Return
        # an explicit flag rather than a payload that looks structured
        # but is empty/garbage (requirement #8).
        is_lab_report = bool(meta) or len(results) >= _MIN_RESULT_LINES_FOR_LAB_REPORT

        return ExtractResponse(
            meta=meta,
            results=results,
            is_lab_report=is_lab_report,
            provider=ocr_result.provider,
        )

    def _extract_meta(self, lines: list[str]) -> dict:
        meta: dict = {}
        for line in lines:
            for field_name, pattern in _META_PATTERNS.items():
                if field_name in meta:
                    continue
                match = pattern.search(line)
                if match:
                    value = match.group(1).strip()
                    if field_name == "report_date":
                        value = normalize_date(value)
                    meta[field_name] = value
        return meta

    def _extract_results(self, lines: list[str]) -> list[ResultRow]:
        results = []
        for line in lines:
            # Skip lines that were already consumed as meta fields.
            if any(p.search(line) for p in _META_PATTERNS.values()):
                continue

            value_match = _VALUE_TOKEN_RE.search(line)
            if not value_match:
                continue

            before = line[: value_match.start()].strip(" :\t-")
            after = line[value_match.end():].strip()

            if not before:
                # No test-name token before the value -> not a result row,
                # likely a stray number (page number, date, etc).
                continue

            unit, reference_range, flag = self._parse_trailing_fields(after)

            results.append(
                ResultRow(
                    test_name=before,
                    value=normalize_value(value_match.group(1)),
                    unit=normalize_unit(unit),
                    reference_range=reference_range,
                    flag=flag,
                    raw_line=line,  # verbatim, per requirement #5
                )
            )
        return results

    @staticmethod
    def _parse_trailing_fields(after: str) -> tuple[str | None, str | None, str | None]:
        """Best-effort split of unit / reference range / flag from the
        text following the value. Anything not confidently identified
        is left as None rather than guessed -- the raw_line still has it."""
        flag = None
        flag_match = re.search(r"\b(H|L|HIGH|LOW|CRITICAL|NORMAL|ABNORMAL)\b", after, re.IGNORECASE)
        if flag_match:
            flag = flag_match.group(1).upper()

        ref_match = re.search(r"([\d.]+\s*[-–]\s*[\d.]+)", after)
        reference_range = ref_match.group(1) if ref_match else None

        remainder = after
        if flag_match:
            remainder = remainder.replace(flag_match.group(0), "")
        if ref_match:
            remainder = remainder.replace(ref_match.group(0), "")
        remainder = remainder.strip(" ,;")

        unit = remainder if remainder else None
        return unit, reference_range, flag
