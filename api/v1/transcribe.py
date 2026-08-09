from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import get_transcription_service
from api.v1.schemas import ErrorResponseModel, TranscribeResponseModel
from core.config import get_settings
from core.errors import DomainError
from services.transcription_service import TranscriptionService
from services.validation import AUDIO_EXTENSIONS, validate_upload

router = APIRouter()


@router.post(
    "/transcribe",
    response_model=TranscribeResponseModel,
    responses={400: {"model": ErrorResponseModel}, 422: {"model": ErrorResponseModel}},
)
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(...),
    service: TranscriptionService = Depends(get_transcription_service),
):
    if language not in ("bn", "en", "auto"):
        raise HTTPException(status_code=422, detail={"error": "language must be one of bn, en, auto", "code": "invalid_language"})

    content = await file.read()
    settings = get_settings()

    try:
        validate_upload(content, file.filename or "", AUDIO_EXTENSIONS, settings.max_upload_mb * 1024 * 1024)
        result = service.transcribe(content, file.filename or "upload", language)
    except DomainError as exc:
        raise HTTPException(status_code=400, detail={"error": exc.message, "code": exc.code}) from exc

    return TranscribeResponseModel(
        transcript=result.transcript,
        detected_language=result.detected_language,
        duration_seconds=result.duration_seconds,
        provider=result.provider,
        speech_detected=result.speech_detected,
    )
