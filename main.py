from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.v1.extract import router as extract_router
from api.v1.transcribe import router as transcribe_router

app = FastAPI(title="Celloscope Speech & Document Extraction", version="0.1.0")

app.include_router(transcribe_router, prefix="/api/v1", tags=["transcription"])
app.include_router(extract_router, prefix="/api/v1", tags=["extraction"])


@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>Celloscope API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 3rem; line-height: 1.6; }
                code { background: #f3f4f6; padding: 0.1rem 0.4rem; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Celloscope API</h1>
            <p>Speech-to-text and lab-report extraction service.</p>
            <ul>
                <li><code>GET /health</code></li>
                <li><code>POST /api/v1/transcribe</code></li>
                <li><code>POST /api/v1/documents/extract</code></li>
            </ul>
            <p>Open the interactive docs at <code>/docs</code>.</p>
        </body>
        </html>
        """
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
