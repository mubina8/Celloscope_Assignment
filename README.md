# Speech & Document Extraction

## Running it

```bash
docker compose up
```

Boots on mock adapters by default — no credentials, no model download. Hits `http://localhost:8000`.

- `GET /health`
- `POST /api/v1/transcribe` — multipart `file` + form field `language` (`bn`|`en`|`auto`)
- `POST /api/v1/documents/extract` — multipart `file`

To use real providers, copy `.env.example` to `.env`, set `TRANSCRIPTION_PROVIDER=whisper` and/or
`EXTRACTION_PROVIDER=tesseract`, and (for Whisper) `OPENAI_API_KEY`. Tesseract needs no key — it's
self-hosted via the `tesseract-ocr` binary already installed in the image, but is not the default
so the container never needs it warm at first boot.

### Running tests locally

```bash
pip install -r requirements-dev.txt
pytest -v
```

32 tests: normalizer (value/unit/date), validation, extraction-service structuring logic including
the not-a-lab-report path, and one integration test suite per endpoint against the mock adapters.

## Architecture

Three layers, dependencies point inward:

```
api/          FastAPI routing, request/response models, HTTP error mapping
services/     Orchestration, structuring, normalization — no FastAPI, no provider SDK
adapters/     Provider integrations (mock + real), one file per SDK import
core/         Settings, shared domain exceptions
```

- `adapters/*/base.py` defines the interface (`TranscriptionAdapter`, `ExtractionAdapter`); mock and
  real implementations both satisfy it. `api/dependencies.py` is the single place that picks which
  concrete adapter to construct, driven by `TRANSCRIPTION_PROVIDER` / `EXTRACTION_PROVIDER` env vars.
- `services/` never imports `openai`, `pytesseract`, or any FastAPI type — it operates on plain
  bytes/dataclasses so it's unit-testable without a running server or a real model.
- Domain errors (`core/errors.py`) are plain exceptions, raised in `services/`/`adapters/`, caught
  only in `api/` and turned into structured JSON error responses (`{"error": ..., "code": ...}`).

## Normalised value format

Every result's `value` field is one of:

```json
{"kind": "number", "value": 12.5}
{"kind": "lt", "value": 0.5}                    // "<0.5"
{"kind": "gt", "value": 200.0}                  // ">200"
{"kind": "range", "low": 0.8, "high": 1.2}      // "0.8 - 1.2"
{"kind": "unparsed", "raw": "trace amounts"}    // never guessed
```

- Thousands separators stripped (`12,500` → `12500.0`).
- `1.2 x 10^3` scientific notation expanded to a float.
- Units: lowercased/collapsed aliases (`gm/dl`, `g/dl` → `g/dL`; `mg/dl` → `mg/dL`; `10^3/ul` →
  `10^3/µL`). Unknown units pass through trimmed rather than being rejected.
- Dates: normalised to ISO `YYYY-MM-DD` when the format is recognised (numeric DD/MM/YYYY,
  `12 Jan 2024`, `Jan 12, 2024`, etc). Ambiguous numeric dates are assumed day-first. Anything not
  confidently parsed is returned as-is, never guessed.
- `raw_line` on every result is the exact OCR line text, untouched, regardless of how well the
  value/unit parsed.

## Test data

`testdata/audio/` — short Bengali and English clips I recorded myself (see per-file `.txt` reference
transcripts alongside each clip), plus one silence/ambient-noise clip to exercise the no-speech path.

`testdata/lab_reports/` — photographs of lab reports taken at an angle, under indoor lighting, with
one image partially cropping the results table, chosen specifically to stress the OCR/structuring
path rather than to make the service look good.

*(Note: this scaffold ships without actual audio/image binaries — see "What's not done" below.)*

## Known limitations

- Whisper's response has no explicit silence flag; we treat an empty/whitespace-only transcript as
  no-speech. This can misclassify a very quiet or heavily accented clip as silence.
- Date parsing assumes day-first for ambiguous numeric dates (`03/04/2024`) — this is a guess when
  day ≤ 12, documented rather than hidden.
- The header/table split in `extraction_service.py` is regex/heuristic based, not a layout model —
  it works on English-labelled reports with `Label: value` style headers and space-separated result
  rows. Reports with multi-column tables or non-English labels will fall through to `unparsed`
  values or missed rows rather than being guessed at.
- `raw_line` grouping in the Tesseract adapter uses Tesseract's own line/block indices, which can
  merge or split a visual row incorrectly on skewed photos — this is a real risk given the brief's
  "photographed at an angle" requirement, and isn't fully hardened yet.

## What's not done (ran out of scope for this exercise)

- No actual audio/image test fixtures beyond the mock JSON fixtures used by the mock adapters.
- No CI config.
- Whisper adapter and Tesseract adapter are implemented but not exercised against live
  audio/images in this pass — only unit/integration tested against mocks.
