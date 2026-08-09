import os

os.environ.setdefault("TRANSCRIPTION_PROVIDER", "mock")
os.environ.setdefault("EXTRACTION_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def test_extract_returns_structured_lab_report():
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("sample_lab_report.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_lab_report"] is True
    assert body["meta"]["patient_name"] == "Jane Doe"
    assert len(body["results"]) > 0
    for row in body["results"]:
        assert "raw_line" in row and row["raw_line"]
        assert "value" in row and "kind" in row["value"]


def test_extract_rejects_oversized_file():
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("huge.jpg", b"x" * (26 * 1024 * 1024), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "file_too_large"


def test_extract_rejects_unsupported_format():
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("report.txt", b"data", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_format"
