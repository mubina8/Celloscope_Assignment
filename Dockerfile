FROM python:3.11-slim

WORKDIR /app

# tesseract-ocr binary is only needed if EXTRACTION_PROVIDER=tesseract,
# but installed unconditionally here for simplicity -- it's cheap and
# does NOT require any model download or credentials, so it doesn't
# violate "no model download required" for the default mock path.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
