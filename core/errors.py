"""
Domain-level exceptions.

These are plain Python exceptions with no FastAPI dependency, so services/
and adapters/ can raise them without importing fastapi. The api/ layer is
the only place that catches these and turns them into HTTP responses.
This is what keeps requirement #10 (no FastAPI types outside api/) true.
"""


class DomainError(Exception):
    """Base class for all expected, handleable errors in this service."""
    code: str = "domain_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnsupportedFormatError(DomainError):
    code = "unsupported_format"


class FileTooLargeError(DomainError):
    code = "file_too_large"


class ProviderError(DomainError):
    """Adapter-level failure (network, auth, model load, etc.)."""
    code = "provider_error"


class NoSpeechDetectedError(DomainError):
    """Raised by transcription adapters when input is silence/ambient noise.

    NOTE: this is *not* treated as a hard error by the service layer --
    see services/transcription_service.py for how it's turned into a
    200 response with empty transcript + a flag, so clients don't have
    to special-case exceptions for a totally normal input.
    """
    code = "no_speech_detected"
