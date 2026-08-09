import os

os.environ.setdefault("TRANSCRIPTION_PROVIDER", "mock")
os.environ.setdefault("EXTRACTION_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def test_transcribe_returns_expected_shape():
    response = client.post(
        "/api/v1/transcribe",
        files={"file": ("sample_bn.wav", b"fake-audio-bytes", "audio/wav")},
        data={"language": "bn"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["detected_language"] == "bn"
    assert body["speech_detected"] is True
    assert isinstance(body["transcript"], str) and body["transcript"]


def test_transcribe_no_speech_input_returns_200_not_error():
    response = client.post(
        "/api/v1/transcribe",
        files={"file": ("silence_clip.wav", b"fake-silence-bytes", "audio/wav")},
        data={"language": "auto"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["speech_detected"] is False
    assert body["transcript"] == ""


def test_transcribe_rejects_unsupported_format():
    response = client.post(
        "/api/v1/transcribe",
        files={"file": ("malware.exe", b"junk", "application/octet-stream")},
        data={"language": "en"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_format"


def test_transcribe_rejects_invalid_language():
    response = client.post(
        "/api/v1/transcribe",
        files={"file": ("clip.wav", b"data", "audio/wav")},
        data={"language": "fr"},
    )
    assert response.status_code == 422
