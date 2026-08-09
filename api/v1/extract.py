from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.dependencies import get_extraction_service
from api.v1.schemas import ErrorResponseModel, ExtractResponseModel, MetaModel, ResultRowModel
from core.config import get_settings
from core.errors import DomainError
from services.extraction_service import ExtractionService
from services.validation import IMAGE_EXTENSIONS, validate_upload

router = APIRouter()


@router.post(
    "/documents/extract",
    response_model=ExtractResponseModel,
    responses={400: {"model": ErrorResponseModel}},
)
async def extract(
    file: UploadFile = File(...),
    service: ExtractionService = Depends(get_extraction_service),
):
    content = await file.read()
    settings = get_settings()

    try:
        validate_upload(content, file.filename or "", IMAGE_EXTENSIONS, settings.max_upload_mb * 1024 * 1024)
        result = service.extract(content, file.filename or "upload")
    except DomainError as exc:
        raise HTTPException(status_code=400, detail={"error": exc.message, "code": exc.code}) from exc

    return ExtractResponseModel(
        meta=MetaModel(**result.meta),
        results=[ResultRowModel(**vars(r)) for r in result.results],
        is_lab_report=result.is_lab_report,
        provider=result.provider,
    )
