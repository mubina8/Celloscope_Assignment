"""
Pure validation logic (requirement #2). Takes plain bytes/filename,
raises core.errors.DomainError subclasses -- the api/ layer maps these
to structured HTTP error responses. Keeping this here (not in api/)
means it's unit-testable without spinning up FastAPI.
"""
from pathlib import Path

from core.errors import FileTooLargeError, UnsupportedFormatError

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".pdf"}


def validate_upload(
    content: bytes,
    filename: str,
    allowed_extensions: set[str],
    max_bytes: int,
) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise UnsupportedFormatError(
            f"Unsupported file format '{ext or '(none)'}'. Allowed: {sorted(allowed_extensions)}"
        )
    if len(content) > max_bytes:
        raise FileTooLargeError(
            f"File is {len(content) / (1024 * 1024):.1f} MB, exceeds limit of {max_bytes / (1024 * 1024):.0f} MB"
        )
