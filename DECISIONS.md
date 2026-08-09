# Decisions

## 1. Whisper API for transcription, not a self-hosted model

**Picked:** OpenAI's Whisper API (`whisper-1`) — handles Bengali + English + auto-detect in one
call, no GPU, no model weights to ship or download.

**Rejected:** self-hosting `faster-whisper` or `whisper.cpp`. Would give offline/no-per-call-cost
transcription, but the brief explicitly requires the default `docker compose up` path to need no
model download — a self-hosted model would either bloat the image with weights or require a
download step on first boot, violating that. Kept as a documented alternative, not built.

## 2. Tesseract for OCR, not a cloud vision API

**Picked:** self-hosted Tesseract via `pytesseract`. No API key needed, so the real-adapter path
can be exercised without a second paid credential in a public repo.

**Rejected:** Google Vision / AWS Textract. Both would likely produce cleaner layout-aware output
(actual table structure) rather than Tesseract's flat line list, which pushed more OCR error
absorption work onto `extraction_service.py`. Traded OCR quality for zero-credential reproducibility,
which the brief weights heavily (10/100 for "runs cleanly, no credentials").

## 3. Structuring logic lives in services/, adapters return only raw lines

**Picked:** `ExtractionAdapter.run_ocr` returns a flat `list[OcrLine]`; all header/table splitting,
regex matching, and value normalization happens in `services/extraction_service.py`.

**Rejected:** letting adapters return pre-structured `meta`/`results` dicts directly, which would
have been less code. Rejected because it would leak business logic (deciding what a "test name" or
"reference range" looks like) into the provider-integration layer, and would mean the mock adapter
and a real OCR adapter would each need to reimplement the same structuring logic — violating the
single-orchestration-point rule the layer separation is meant to enforce.

## 4. Silence/no-speech is a `200` response, not an error

**Picked:** `TranscriptionResult.speech_detected: bool` + empty transcript, still `200 OK`.

**Rejected:** raising an exception (e.g. `422 no_speech_detected`) that the client must catch.
Silence is not malformed input — it's a normal, expected outcome for real-world audio (dead air,
recording artifacts). Treating it as an HTTP error would force every client to special-case
try/catch around a totally valid request. `core/errors.py` still defines
`NoSpeechDetectedError` for adapters that want to signal it that way internally, but the service
boundary converts it to a result, not a raised exception — documented in the docstring so this
isn't a silent inconsistency between adapter and service behavior.

## 5. Non-lab-report images degrade via an `is_lab_report: bool` flag, not a 4xx

**Picked:** `POST /documents/extract` always returns `200` with `is_lab_report: false` and empty
`meta`/`results` when the heuristic (no meta fields found AND no result rows found) fails to match.

**Rejected:** returning `400`/`422` for "this doesn't look like a lab report." A photo that's
genuinely a lab report but badly angled/lit might legitimately fail to match some fields without
being garbage — an error response would conflate "wrong document type" with "partial extraction,"
which are different failure modes a client needs to handle differently. The boolean flag lets a
client distinguish "nothing usable, try a different photo" from "we got what we could, some fields
are missing" (the latter simply shows up as `null` fields in `meta`, not an error).
