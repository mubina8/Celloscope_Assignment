import pytest

from core.errors import FileTooLargeError, UnsupportedFormatError
from services.validation import AUDIO_EXTENSIONS, validate_upload


def test_accepts_supported_format():
    validate_upload(b"data", "clip.wav", AUDIO_EXTENSIONS, max_bytes=1000)  # no raise


def test_rejects_unsupported_format():
    with pytest.raises(UnsupportedFormatError):
        validate_upload(b"data", "clip.exe", AUDIO_EXTENSIONS, max_bytes=1000)


def test_rejects_oversized_file():
    with pytest.raises(FileTooLargeError):
        validate_upload(b"x" * 2000, "clip.wav", AUDIO_EXTENSIONS, max_bytes=1000)


def test_rejects_missing_extension():
    with pytest.raises(UnsupportedFormatError):
        validate_upload(b"data", "clip", AUDIO_EXTENSIONS, max_bytes=1000)
