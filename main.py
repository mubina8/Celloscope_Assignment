from fastapi import FastAPI

from api.v1.extract import router as extract_router
from api.v1.transcribe import router as transcribe_router

app = FastAPI(title="Celloscope Speech & Document Extraction", version="0.1.0")

app.include_router(transcribe_router, prefix="/api/v1", tags=["transcription"])
app.include_router(extract_router, prefix="/api/v1", tags=["extraction"])


@app.get("/health")
async def health():
    return {"status": "ok"}
