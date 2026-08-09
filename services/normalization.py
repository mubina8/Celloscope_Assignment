"""
Normalises raw OCR text fragments for lab report values, units, and dates
into a canonical form.

Design (documented in README too):

VALUE canonical form -> one of:
  - {"kind": "number", "value": <float>}
  - {"kind": "lt", "value": <float>}        # "<0.5"
  - {"kind": "gt", "value": <float>}        # ">200"
  - {"kind": "range", "low": <float>, "high": <float>}   # "0.8 - 1.2"
  - {"kind": "unparsed", "raw": "<original text>"}       # never guess

Rules:
  - Thousands separators (12,500 -> 12500) are stripped.
  - Scientific/"x 10^n" notation (1.2 x 10^3) is expanded to a float.
  - Anything not matching a known pattern is preserved verbatim as
    kind="unparsed" -- per requirement #7/"what does not earn points",
    we do not guess.

UNIT canonical form: lowercased, "gm/dl" and "g/dl" collapse to "g/dL";
"µL"/"uL"/"ul" collapse to "µL"; internal whitespace stripped. Unknown
units are passed through lowercased+trimmed rather than rejected --
extraction should not fail the whole row over an unfamiliar unit.

DATE canonical form: ISO 8601 "YYYY-MM-DD" when the format is
recognised (dd/mm/yyyy, dd-mm-yyyy, "12 Jan 2024", "Jan 12, 2024",
yyyy-mm-dd). Ambiguous numeric dates (e.g. 03/04/2024) are assumed
day/month/year, since these are lab reports and the target market
convention is DMY -- documented as a known limitation because it is a
guess when day <= 12.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

_THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3}(\D|$))")
_SCI_NOTATION_RE = re.compile(r"^\s*([\d.]+)\s*[xX×]\s*10\s*\^?\s*(-?\d+)\s*$")
_RANGE_RE = re.compile(r"^\s*([\d.]+)\s*[-–]\s*([\d.]+)\s*$")
_LT_RE = re.compile(r"^\s*<\s*([\d.]+)\s*$")
_GT_RE = re.compile(r"^\s*>\s*([\d.]+)\s*$")
_PLAIN_NUMBER_RE = re.compile(r"^\s*-?[\d.]+\s*$")

_UNIT_ALIASES = {
    "gm/dl": "g/dL",
    "g/dl": "g/dL",
    "mg/dl": "mg/dL",
    "mmol/l": "mmol/L",
    "10^3/ul": "10^3/µL",
    "10^3/µl": "10^3/µL",
    "x10^3/ul": "10^3/µL",
}

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d.%m.%Y",
]


def normalize_value(raw: str) -> dict[str, Any]:
    """Normalise a raw value fragment. Never raises; unparsable input
    comes back as {"kind": "unparsed", "raw": raw}."""
    if raw is None:
        return {"kind": "unparsed", "raw": raw}

    text = raw.strip()
    if not text:
        return {"kind": "unparsed", "raw": raw}

    cleaned = _THOUSANDS_RE.sub("", text)

    sci_match = _SCI_NOTATION_RE.match(cleaned)
    if sci_match:
        mantissa, exponent = sci_match.groups()
        try:
            return {"kind": "number", "value": float(mantissa) * (10 ** int(exponent))}
        except ValueError:
            return {"kind": "unparsed", "raw": raw}

    range_match = _RANGE_RE.match(cleaned)
    if range_match:
        low, high = range_match.groups()
        try:
            return {"kind": "range", "low": float(low), "high": float(high)}
        except ValueError:
            return {"kind": "unparsed", "raw": raw}

    lt_match = _LT_RE.match(cleaned)
    if lt_match:
        try:
            return {"kind": "lt", "value": float(lt_match.group(1))}
        except ValueError:
            return {"kind": "unparsed", "raw": raw}

    gt_match = _GT_RE.match(cleaned)
    if gt_match:
        try:
            return {"kind": "gt", "value": float(gt_match.group(1))}
        except ValueError:
            return {"kind": "unparsed", "raw": raw}

    if _PLAIN_NUMBER_RE.match(cleaned):
        try:
            return {"kind": "number", "value": float(cleaned)}
        except ValueError:
            return {"kind": "unparsed", "raw": raw}

    return {"kind": "unparsed", "raw": raw}


def normalize_unit(raw: str | None) -> str | None:
    """Canonicalise a unit string. Unknown units pass through
    lowercased+trimmed rather than being rejected."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    key = text.lower().replace(" ", "")
    return _UNIT_ALIASES.get(key, text.strip())


def normalize_date(raw: str | None) -> str | None:
    """Return ISO 8601 'YYYY-MM-DD', or the original string if it
    cannot be confidently parsed (never guessed at)."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return text
